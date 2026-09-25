"""Minimal idempotency and status metadata for a human WhatsApp send."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKeyConstraint,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ManualSendReceipt(Base):
    __tablename__ = "manual_send_receipts"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'accepted', 'uncertain')", name="ck_manual_send_status"
        ),
        UniqueConstraint(
            "branch_id", "conversation_id", "request_id", name="uq_manual_send_request"
        ),
        ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_manual_send_conversation_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_manual_send_actor_branch",
            ondelete="RESTRICT",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    request_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    provider_message_id: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
