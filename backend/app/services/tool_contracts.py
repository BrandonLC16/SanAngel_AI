"""Strict Responses API tool schemas and backend-only call validation."""

import json
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from backend.app.core.config import AssistantSettings
from backend.app.schemas.price import normalize_price_unit
from backend.app.services.branch_scope import BranchScope
from backend.app.services.faq_service import MAX_FAQ_QUERY_CHARS

MAX_TOOL_ARGUMENT_BYTES = 4096
MAX_PRODUCT_ID = 2**63 - 1
UNIT_PATTERN = r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$"
type ToolName = Literal["get_product_price", "get_branch_info", "search_faq", "request_human_help"]
type HumanHelpReason = Literal["customer_requested", "faq_unknown", "faq_ambiguous"]


class ToolCallValidationError(ValueError):
    """A tool name or its arguments failed the closed backend contract."""


class _ToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True, hide_input_in_errors=True)


class GetProductPriceArguments(_ToolArguments):
    product_id: int = Field(gt=0, le=MAX_PRODUCT_ID)
    unit: str = Field(min_length=1, max_length=24, pattern=UNIT_PATTERN)

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        if value != normalize_price_unit(value):
            raise ValueError("unit must be a lowercase code without surrounding whitespace")
        return value


class GetBranchInfoArguments(_ToolArguments):
    pass


class SearchFAQArguments(_ToolArguments):
    query: str = Field(min_length=1, max_length=MAX_FAQ_QUERY_CHARS)

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = unicodedata.normalize("NFKC", value).strip()
        if (
            not normalized
            or len(normalized) > MAX_FAQ_QUERY_CHARS
            or not normalized.isprintable()
            or not any(character.isalnum() for character in normalized)
        ):
            raise ValueError("FAQ query has an invalid format")
        return normalized


class RequestHumanHelpArguments(_ToolArguments):
    reason: HumanHelpReason


type ToolArguments = (
    GetProductPriceArguments
    | GetBranchInfoArguments
    | SearchFAQArguments
    | RequestHumanHelpArguments
)


@dataclass(frozen=True, slots=True)
class ValidatedToolCall:
    """Validated model arguments bound to the backend-configured branch."""

    name: ToolName
    arguments: ToolArguments
    branch_scope: BranchScope


_ARGUMENT_MODELS: dict[str, type[_ToolArguments]] = {
    "get_product_price": GetProductPriceArguments,
    "get_branch_info": GetBranchInfoArguments,
    "search_faq": SearchFAQArguments,
    "request_human_help": RequestHumanHelpArguments,
}

_TOOL_SCHEMAS: tuple[dict[str, object], ...] = (
    {
        "type": "function",
        "name": "get_product_price",
        "description": "Get the current exact price for a product and unit in this branch.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "product_id": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": MAX_PRODUCT_ID,
                    "description": "ID of an existing product in the configured branch.",
                },
                "unit": {
                    "type": "string",
                    "pattern": UNIT_PATTERN,
                    "description": "Lowercase internal unit code, such as kg or piece.",
                },
            },
            "required": ["product_id", "unit"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "get_branch_info",
        "description": "Get the configured branch's verified address, phone and business hours.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "search_faq",
        "description": "Search validated FAQ data for a customer's question in this branch.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Customer question, up to 240 characters.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "type": "function",
        "name": "request_human_help",
        "description": "Propose human help without contacting staff or confirming a handoff.",
        "strict": True,
        "parameters": {
            "type": "object",
            "properties": {
                "reason": {
                    "type": "string",
                    "enum": ["customer_requested", "faq_unknown", "faq_ambiguous"],
                    "description": "Fixed reason code; do not include customer details.",
                }
            },
            "required": ["reason"],
            "additionalProperties": False,
        },
    },
)


def get_tool_schemas() -> list[dict[str, object]]:
    """Return an isolated copy of the four allowed Responses API function schemas."""

    return deepcopy(list(_TOOL_SCHEMAS))


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-standard JSON constant")


def validate_tool_call(
    name: str, arguments_json: str, *, assistant_settings: AssistantSettings
) -> ValidatedToolCall:
    """Check allowlist and arguments before binding the backend-owned branch scope."""

    model = _ARGUMENT_MODELS.get(name) if isinstance(name, str) else None
    if model is None:
        raise ToolCallValidationError("unsupported tool")
    if not isinstance(arguments_json, str):
        raise ToolCallValidationError("invalid tool arguments")
    try:
        if len(arguments_json.encode("utf-8")) > MAX_TOOL_ARGUMENT_BYTES:
            raise ValueError("oversized arguments")
        payload = json.loads(
            arguments_json,
            object_pairs_hook=_unique_keys,
            parse_constant=_reject_json_constant,
        )
        arguments = model.model_validate(payload)
    except (UnicodeError, ValueError, ValidationError, RecursionError):
        raise ToolCallValidationError("invalid tool arguments") from None
    if not isinstance(assistant_settings, AssistantSettings):
        raise ToolCallValidationError("trusted branch configuration is required")
    return ValidatedToolCall(
        name=name,
        arguments=arguments,
        branch_scope=BranchScope.from_settings(assistant_settings),
    )
