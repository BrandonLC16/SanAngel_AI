"""Short-lived, encrypted work accepted before acknowledging a webhook."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class WhatsAppInboundJob(Base):
    __tablename__ = "whatsapp_inbound_jobs"
    __table_args__ = (
        CheckConstraint(
            "(status = 'pending' AND claimed_at IS NULL) OR "
            "(status IN ('processing', 'uncertain') AND claimed_at IS NOT NULL)",
            name="ck_whatsapp_inbound_jobs_status",
        ),
        UniqueConstraint(
            "branch_id", "provider_message_id", name="uq_whatsapp_inbound_jobs_branch_message"
        ),
        Index("ix_whatsapp_inbound_jobs_branch_status_time", "branch_id", "status", "enqueued_at"),
        Index("ix_whatsapp_inbound_jobs_branch_sender", "branch_id", "sender_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    provider_message_id: Mapped[str] = mapped_column(String(512), nullable=False)
    sender_key: Mapped[str] = mapped_column(String(64), nullable=False)
    payload_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(12), nullable=False, default="pending")
    enqueued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
