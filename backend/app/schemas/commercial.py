"""Immutable outputs returned by read-only commercial queries."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CommercialResult(BaseModel):
    """Base for detached, immutable commercial response data."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class BranchInfo(CommercialResult):
    name: str
    address: str
    phone: str | None
    business_hours: str


class ProductSummary(CommercialResult):
    product_id: int
    name: str
    category: str


class ProductPriceInfo(CommercialResult):
    product_id: int
    product_name: str
    category: str
    amount: Decimal
    unit: str
    updated_at: datetime
