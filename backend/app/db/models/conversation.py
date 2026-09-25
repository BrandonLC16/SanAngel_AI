"""Minimal branch-scoped WhatsApp conversation identity."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Conversation(Base):
    """Correlate one sender without storing a plain phone number or message text."""

    __tablename__ = "conversations"
    __table_args__ = (
        CheckConstraint("channel = 'whatsapp'", name="ck_conversations_channel"),
        CheckConstraint(
            "length(external_user_key) = 64 AND external_user_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_conversations_external_user_key",
        ),
        UniqueConstraint(
            "branch_id", "channel", "external_user_key", name="uq_conversations_branch_channel_user"
        ),
        UniqueConstraint("id", "branch_id", name="uq_conversations_id_branch_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    channel: Mapped[str] = mapped_column(String(16), nullable=False, default="whatsapp")
    external_user_key: Mapped[str] = mapped_column(String(64), nullable=False)
    recipient_ciphertext: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )
