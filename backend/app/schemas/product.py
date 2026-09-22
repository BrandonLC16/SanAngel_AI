"""Validated product catalog inputs."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProductData(BaseModel):
    """Fields accepted when creating or updating a product."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)

    @field_validator("name", "category")
    @classmethod
    def validate_catalog_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or not any(character.isalnum() for character in normalized):
            raise ValueError("catalog text must contain letters or numbers")
        if not normalized.isprintable():
            raise ValueError("catalog text must not contain control characters")
        return normalized
