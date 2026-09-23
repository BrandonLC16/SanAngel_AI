import asyncio
import json
import re
from collections.abc import Awaitable
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, Protocol

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)
from pydantic import TypeAdapter

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AIProviderConnectionError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderResponseError,
    AIProviderStatusError,
    AIProviderTimeoutError,
    BranchNotConfiguredError,
    InvalidRequestError,
)
from backend.app.services.tool_contracts import ToolCallValidationError, get_tool_schemas
from backend.app.services.tool_dispatcher import ToolDispatcher, ToolResult

MAX_TOOL_ROUNDS = 3
MAX_CALLS_PER_RESPONSE = 4
MAX_RESPONSE_ITEMS = 16
MAX_TOOL_OUTPUT_BYTES = 8192
MAX_TOOL_RESPONSE_TOKENS = 1024
_CALL_ID_PATTERN = re.compile(r"[A-Za-z0-9_-]{1,128}")
_TOOL_RESULT_ADAPTER = TypeAdapter(ToolResult)


@dataclass(frozen=True, slots=True)
class _FunctionCall:
    name: str
    arguments: str
    call_id: str


class ResponseResult(Protocol):
    output_text: str
    output: list[object]
    status: str


class ResponsesAPI(Protocol):
    def create(self, **kwargs: Any) -> Awaitable[ResponseResult]: ...


class OpenAIClient(Protocol):
    responses: ResponsesAPI


def load_base_system_prompt() -> str:
    """Load the versioned base instructions shipped with the application."""

    prompt = (
        files("backend.app.prompts")
        .joinpath("base_system_prompt.txt")
        .read_text(encoding="utf-8")
        .strip()
    )
    if not prompt:
        raise RuntimeError("base system prompt must not be empty")
    return prompt


class OpenAIService:
    """Isolate the OpenAI Responses API behind an application-owned interface."""

    def __init__(
        self,
        settings: Settings,
        *,
        client: OpenAIClient | None = None,
        system_prompt: str | None = None,
    ) -> None:
        self._model = settings.openai_model
        self._store_responses = settings.openai_store_responses
        self._assistant_branch_code = settings.assistant_branch_code
        self._max_message_chars = settings.chat_max_message_chars
        self._system_prompt = system_prompt or load_base_system_prompt()
        self._client = (
            client
            if client is not None
            else AsyncOpenAI(
                api_key=settings.openai_api_key.get_secret_value(),
                timeout=settings.openai_timeout_seconds,
                max_retries=settings.openai_max_retries,
            )
        )

    async def generate_reply(self, message: str) -> str:
        """Generate plain text using the Responses API without logging request contents."""

        response = await self._create_response(
            model=self._model,
            instructions=self._system_prompt,
            input=message,
            store=self._store_responses,
        )

        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise AIProviderResponseError("AI provider returned no text")
        return output_text.strip()

    async def generate_reply_with_tools(self, message: str, dispatcher: ToolDispatcher) -> str:
        """Run bounded Responses function calls with stateless, scoped tool outputs."""

        if (
            not isinstance(message, str)
            or not message.strip()
            or len(message) > self._max_message_chars
        ):
            raise InvalidRequestError("chat message violates configured length limit")
        if not isinstance(dispatcher, ToolDispatcher) or (
            dispatcher.branch_scope.branch_code != self._assistant_branch_code
        ):
            raise BranchNotConfiguredError("tool dispatcher branch does not match assistant")

        input_items: list[object] = [{"role": "user", "content": message.strip()}]
        for round_index in range(MAX_TOOL_ROUNDS + 1):
            response = await self._create_response(
                model=self._model,
                instructions=self._system_prompt,
                input=list(input_items),
                store=self._store_responses,
                tools=get_tool_schemas(),
                parallel_tool_calls=False,
                max_output_tokens=MAX_TOOL_RESPONSE_TOKENS,
            )
            output_items, calls = _read_response(response)
            if not calls:
                if not any(getattr(item, "type", None) == "message" for item in output_items):
                    raise AIProviderResponseError("AI provider returned no final message")
                output_text = getattr(response, "output_text", None)
                if not isinstance(output_text, str) or not output_text.strip():
                    raise AIProviderResponseError("AI provider returned no final text")
                return output_text.strip()
            if round_index == MAX_TOOL_ROUNDS:
                raise AIProviderResponseError("tool call round limit exceeded")

            # Replay every output item, including reasoning, when store=False.
            input_items.extend(output_items)
            for call in calls:
                try:
                    result = await asyncio.to_thread(dispatcher.dispatch, call.name, call.arguments)
                except ToolCallValidationError:
                    raise AIProviderResponseError(
                        "AI provider returned an invalid tool call"
                    ) from None
                input_items.append(
                    {
                        "type": "function_call_output",
                        "call_id": call.call_id,
                        "output": _serialize_tool_result(result),
                    }
                )
        raise AIProviderResponseError("tool call round limit exceeded")

    async def _create_response(self, **kwargs: Any) -> ResponseResult:
        try:
            return await self._client.responses.create(**kwargs)
        except APITimeoutError as exc:
            raise AIProviderTimeoutError("AI provider timeout") from exc
        except RateLimitError as exc:
            raise AIProviderRateLimitError("AI provider rate limit") from exc
        except APIConnectionError as exc:
            raise AIProviderConnectionError("AI provider connection failure") from exc
        except APIStatusError as exc:
            raise AIProviderStatusError("AI provider HTTP failure") from exc
        except APIError as exc:
            raise AIProviderError("AI provider failure") from exc


def _read_response(response: ResponseResult) -> tuple[list[object], tuple[_FunctionCall, ...]]:
    """Reject unexpected output shapes before executing any calls from that response."""

    output = getattr(response, "output", None)
    if (
        getattr(response, "status", None) != "completed"
        or not isinstance(output, list)
        or len(output) > MAX_RESPONSE_ITEMS
    ):
        raise AIProviderResponseError("AI provider returned an incomplete tool response")

    calls: list[_FunctionCall] = []
    seen_call_ids: set[str] = set()
    for item in output:
        item_type = getattr(item, "type", None)
        if item_type in {"message", "reasoning"}:
            continue
        if item_type != "function_call":
            raise AIProviderResponseError("AI provider returned an unsupported output item")
        name = getattr(item, "name", None)
        arguments = getattr(item, "arguments", None)
        call_id = getattr(item, "call_id", None)
        if (
            not isinstance(name, str)
            or not isinstance(arguments, str)
            or not isinstance(call_id, str)
            or _CALL_ID_PATTERN.fullmatch(call_id) is None
            or call_id in seen_call_ids
        ):
            raise AIProviderResponseError("AI provider returned a malformed function call")
        seen_call_ids.add(call_id)
        calls.append(_FunctionCall(name=name, arguments=arguments, call_id=call_id))
        if len(calls) > MAX_CALLS_PER_RESPONSE:
            raise AIProviderResponseError("AI provider returned too many function calls")
    return output, tuple(calls)


def _serialize_tool_result(result: ToolResult) -> str:
    payload = json.dumps(
        {"result": _TOOL_RESULT_ADAPTER.dump_python(result, mode="json")},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    if len(payload.encode("utf-8")) > MAX_TOOL_OUTPUT_BYTES:
        raise AIProviderResponseError("tool result exceeds output limit")
    return payload
