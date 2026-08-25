from collections.abc import Awaitable
from importlib.resources import files
from typing import Protocol

from openai import (
    APIConnectionError,
    APIError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AIProviderConnectionError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderResponseError,
    AIProviderStatusError,
    AIProviderTimeoutError,
)


class ResponseResult(Protocol):
    output_text: str


class ResponsesAPI(Protocol):
    def create(
        self,
        *,
        model: str,
        instructions: str,
        input: str,
        store: bool,
    ) -> Awaitable[ResponseResult]: ...


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

        try:
            response = await self._client.responses.create(
                model=self._model,
                instructions=self._system_prompt,
                input=message,
                store=self._store_responses,
            )
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

        output_text = getattr(response, "output_text", None)
        if not isinstance(output_text, str) or not output_text.strip():
            raise AIProviderResponseError("AI provider returned no text")
        return output_text.strip()
