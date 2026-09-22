"""Branch persistence model."""

from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Branch(Base):
    """Business information owned by one branch-scoped assistant installation."""

    __tablename__ = "branches"
    __table_args__ = (
        CheckConstraint("length(code) BETWEEN 2 AND 48", name="ck_branches_code_length"),
        CheckConstraint("code = lower(code)", name="ck_branches_code_lowercase"),
        CheckConstraint(
            "code NOT GLOB '*[^a-z0-9-]*'",
            name="ck_branches_code_characters",
        ),
        CheckConstraint(
            "substr(code, 1, 1) GLOB '[a-z]'",
            name="ck_branches_code_prefix",
        ),
        CheckConstraint("substr(code, -1, 1) <> '-'", name="ck_branches_code_suffix"),
        CheckConstraint("instr(code, '--') = 0", name="ck_branches_code_hyphens"),
        CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 120",
            name="ck_branches_name_length",
        ),
        CheckConstraint(
            "length(trim(address)) BETWEEN 1 AND 300",
            name="ck_branches_address_length",
        ),
        CheckConstraint(
            "phone IS NULL OR (length(phone) BETWEEN 9 AND 16 AND phone = trim(phone))",
            name="ck_branches_phone_length",
        ),
        CheckConstraint(
            "length(trim(business_hours)) BETWEEN 1 AND 500",
            name="ck_branches_business_hours_length",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(16), nullable=True)
    business_hours: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
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
