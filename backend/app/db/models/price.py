"""Exact branch-scoped product price persistence model."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Price(Base):
    """The current exact price for one product, branch, and unit."""

    __tablename__ = "prices"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_prices_amount_non_negative"),
        CheckConstraint(
            "amount <= 9999999999.99",
            name="ck_prices_amount_maximum",
        ),
        CheckConstraint(
            "round(amount, 2) = amount",
            name="ck_prices_amount_scale",
        ),
        CheckConstraint(
            "length(unit) BETWEEN 1 AND 24",
            name="ck_prices_unit_length",
        ),
        CheckConstraint("unit = lower(unit)", name="ck_prices_unit_lowercase"),
        CheckConstraint(
            "unit NOT GLOB '*[^a-z0-9-]*'",
            name="ck_prices_unit_characters",
        ),
        CheckConstraint(
            "substr(unit, 1, 1) GLOB '[a-z]'",
            name="ck_prices_unit_prefix",
        ),
        CheckConstraint("substr(unit, -1, 1) <> '-'", name="ck_prices_unit_suffix"),
        CheckConstraint("instr(unit, '--') = 0", name="ck_prices_unit_hyphens"),
        ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_prices_branch_id_branches",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["product_id", "branch_id"],
            ["products.id", "products.branch_id"],
            name="fk_prices_product_id_branch_id_products",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "branch_id",
            "product_id",
            "unit",
            name="uq_prices_branch_id_product_id_unit",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    unit: Mapped[str] = mapped_column(String(24), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
