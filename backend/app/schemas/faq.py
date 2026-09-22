"""Versioned FAQ table contract; records are data scoped by backend configuration."""

from collections.abc import Sequence
from enum import StrEnum
from typing import Literal
from unicodedata import category as unicode_category

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.config import validate_branch_code

FAQ_TSV_COLUMNS = ("schema_version", "branch_code", "category", "question", "answer")


class FAQCategory(StrEnum):
    GENERAL = "general"
    SERVICIOS = "servicios"
    PAGOS = "pagos"
    ENTREGAS = "entregas"
    POLITICAS = "politicas"


class FAQSourceRow(BaseModel):
    """Untrusted values from one tabular FAQ row, before branch authorization."""

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    schema_version: Literal["1"]
    branch_code: str = Field(min_length=2, max_length=48)
    category: FAQCategory
    question: str = Field(min_length=1, max_length=240)
    answer: str = Field(min_length=1, max_length=1200)

    @field_validator("branch_code")
    @classmethod
    def validate_scope_code(cls, value: str) -> str:
        return validate_branch_code(value)

    @field_validator("question", "answer")
    @classmethod
    def validate_plain_text(cls, value: str) -> str:
        if value != value.strip() or any(unicode_category(char) == "Cc" for char in value):
            raise ValueError("FAQ text must be trimmed plain text without control characters")
        return value


def validate_faq_columns(columns: Sequence[str] | None) -> None:
    """Require one exact, versioned TSV header before accepting rows."""

    if tuple(columns or ()) != FAQ_TSV_COLUMNS:
        raise ValueError("FAQ table columns do not match the supported format")
