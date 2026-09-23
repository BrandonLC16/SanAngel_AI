"""Minimal durable metadata for confirmed Excel price import attempts."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class PriceImportAudit(Base):
    __tablename__ = "price_import_audits"
    __table_args__ = (
        UniqueConstraint("attempt_id", name="uq_price_import_audits_attempt_id"),
        CheckConstraint(
            "status IN ('success', 'rejected', 'failed')",
            name="ck_price_import_audits_status",
        ),
        CheckConstraint(
            "created_count >= 0 AND updated_count >= 0 AND unchanged_count >= 0 "
            "AND error_count >= 0",
            name="ck_price_import_audits_counts",
        ),
        Index("ix_price_import_audits_branch_time", "branch_code", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(String(32), nullable=False)
    branch_code: Mapped[str] = mapped_column(String(48), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(64), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    file_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False)
    created_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unchanged_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    errors_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
