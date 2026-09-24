"""Message chronology without persisting customer text."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Message(Base):
    """Record direction and time only within a branch-owned conversation."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint("direction IN ('inbound', 'outbound')", name="ck_messages_direction"),
        ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_messages_conversation_id_branch_id_conversations",
            ondelete="RESTRICT",
        ),
        Index(
            "ix_messages_branch_conversation_time", "branch_id", "conversation_id", "occurred_at"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    conversation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    direction: Mapped[str] = mapped_column(String(8), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
