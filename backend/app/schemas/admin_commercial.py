"""Strict public admin commercial payloads without a caller-supplied branch."""

from decimal import Decimal
from unicodedata import category as unicode_category

from pydantic import BaseModel, ConfigDict, Field, StrictBool, field_validator

from backend.app.schemas.branch import BranchData
from backend.app.schemas.faq import FAQCategory
from backend.app.schemas.price import PriceData
from backend.app.schemas.product import ProductData
from backend.app.services.faq_service import normalize_faq_question


class _StrictPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class BranchUpdate(_StrictPayload):
    name: str = Field(min_length=1, max_length=120)
    address: str = Field(min_length=1, max_length=300)
    phone: str | None = Field(default=None, max_length=16)
    business_hours: str = Field(min_length=1, max_length=500)

    @field_validator("name", "address", "business_hours")
    @classmethod
    def validate_business_text(cls, value: str) -> str:
        return BranchData.normalize_business_text(value)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        return BranchData.validate_phone(value)


class BranchView(_StrictPayload):
    code: str
    name: str
    address: str
    phone: str | None
    business_hours: str


class ProductUpdate(_StrictPayload):
    name: str = Field(min_length=1, max_length=120)
    category: str = Field(min_length=1, max_length=80)
    is_active: StrictBool

    @field_validator("name", "category")
    @classmethod
    def validate_catalog_text(cls, value: str) -> str:
        return ProductData.validate_catalog_text(value)


class ProductView(_StrictPayload):
    id: int
    name: str
    category: str
    is_active: bool


class PriceWrite(_StrictPayload):
    amount: Decimal = Field(ge=Decimal("0"), max_digits=12, decimal_places=2, allow_inf_nan=False)

    @field_validator("amount", mode="before")
    @classmethod
    def reject_float(cls, value: object) -> object:
        return PriceData.reject_binary_floats(value)


class PriceView(_StrictPayload):
    id: int
    product_id: int
    unit: str
    amount: Decimal


class FAQWrite(_StrictPayload):
    category: FAQCategory
    question: str = Field(min_length=1, max_length=240)
    answer: str = Field(min_length=1, max_length=1200)
    is_active: StrictBool = True

    @field_validator("question", "answer")
    @classmethod
    def validate_text(cls, value: str) -> str:
        if value != value.strip() or any(unicode_category(char) == "Cc" for char in value):
            raise ValueError("FAQ text must be trimmed plain text without control characters")
        if not any(character.isalnum() for character in value):
            raise ValueError("FAQ text must contain letters or numbers")
        return value

    @field_validator("question")
    @classmethod
    def validate_key(cls, value: str) -> str:
        question_key = normalize_faq_question(value)
        if not question_key or len(question_key) > 240:
            raise ValueError("FAQ question has no searchable content")
        return value


class FAQView(_StrictPayload):
    id: int
    category: FAQCategory
    question: str
    answer: str
    is_active: bool
