"""Minimal persistent receipt shape for a WhatsApp inbound event."""

from datetime import datetime

from sqlalchemy import (
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


class WhatsAppEventReceipt(Base):
    """Retain an event ID and processing state, never its webhook payload."""

    __tablename__ = "whatsapp_event_receipts"
    __table_args__ = (
        CheckConstraint(
            "length(provider_message_id) BETWEEN 1 AND 512 "
            "AND provider_message_id = trim(provider_message_id)",
            name="ck_whatsapp_event_receipts_message_id",
        ),
        CheckConstraint(
            "(status = 'claimed' AND completed_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_whatsapp_event_receipts_status",
        ),
        UniqueConstraint(
            "branch_id", "provider_message_id", name="uq_whatsapp_event_receipts_branch_message"
        ),
        Index(
            "ix_whatsapp_event_receipts_branch_status_time", "branch_id", "status", "received_at"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    provider_message_id: Mapped[str] = mapped_column(String(512), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="claimed")
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
