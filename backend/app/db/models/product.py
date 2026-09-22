"""Branch-scoped product persistence model."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Product(Base):
    """A catalog item whose availability belongs to exactly one branch."""

    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 120",
            name="ck_products_name_length",
        ),
        CheckConstraint(
            "length(trim(category)) BETWEEN 1 AND 80",
            name="ck_products_category_length",
        ),
        UniqueConstraint(
            "branch_id",
            "name",
            name="uq_products_branch_id_name",
        ),
        UniqueConstraint(
            "id",
            "branch_id",
            name="uq_products_id_branch_id",
        ),
        Index(
            "ix_products_branch_catalog",
            "branch_id",
            "is_active",
            "category",
            "name",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
    )
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
