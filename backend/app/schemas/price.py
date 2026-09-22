"""Validated exact monetary inputs for branch-scoped prices."""

import re
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator

PRICE_UNIT_PATTERN = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*")


def normalize_price_unit(value: str) -> str:
    """Normalize a compact internal unit code without accepting arbitrary text."""

    if not isinstance(value, str):
        raise ValueError("unit must be a string")
    normalized = value.strip().lower()
    if len(normalized) > 24 or PRICE_UNIT_PATTERN.fullmatch(normalized) is None:
        raise ValueError("unit must be a valid lowercase code")
    return normalized


class PriceData(BaseModel):
    """Fields accepted when creating or updating one current price."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    amount: Decimal = Field(
        ge=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        allow_inf_nan=False,
    )
    unit: str = Field(min_length=1, max_length=24)

    @field_validator("amount", mode="before")
    @classmethod
    def reject_binary_floats(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("amount must not be provided as a binary float")
        return value

    @field_validator("unit")
    @classmethod
    def validate_unit(cls, value: str) -> str:
        return normalize_price_unit(value)
