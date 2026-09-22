import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.core.config import validate_branch_code

BRANCH_PHONE_PATTERN = re.compile(r"\+[1-9][0-9]{7,14}")


class BranchData(BaseModel):
    """Validated business data for one branch installation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    code: str = Field(min_length=2, max_length=48)
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=300)
    phone: str | None = Field(default=None, max_length=16)
    business_hours: str = Field(min_length=1, max_length=500)

    @field_validator("code")
    @classmethod
    def validate_code(cls, value: str) -> str:
        return validate_branch_code(value)

    @field_validator("name", "address", "business_hours")
    @classmethod
    def normalize_business_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("business text must not be blank")
        return normalized

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value != value.strip() or BRANCH_PHONE_PATTERN.fullmatch(value) is None:
            raise ValueError("phone must use E.164 format")
        return value


class AssistantProfile(BaseModel):
    """Versioned installation payload containing data for exactly one branch."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    branch: BranchData
