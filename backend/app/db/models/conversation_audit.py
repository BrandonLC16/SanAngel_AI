"""Short-lived, content-free audit events for human conversation handling."""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKeyConstraint, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ConversationAudit(Base):
    __tablename__ = "conversation_audits"
    __table_args__ = (
        CheckConstraint(
            "(action = 'help_requested' AND actor_user_id IS NULL "
            "AND reason IN ('customer_requested', 'ai_unavailable') "
            "AND manual_send_receipt_id IS NULL) OR "
            "(action IN ('take', 'release') AND actor_user_id IS NOT NULL "
            "AND reason IS NULL AND manual_send_receipt_id IS NULL) OR "
            "(action IN ('send_pending', 'send_accepted', 'send_uncertain') "
            "AND actor_user_id IS NOT NULL AND reason IS NULL "
            "AND manual_send_receipt_id IS NOT NULL)",
            name="ck_conversation_audits_action_context",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_conversation_audits_conversation_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_conversation_audits_actor_branch",
            ondelete="RESTRICT",
        ),
        Index("ix_conversation_audits_branch_time", "branch_id", "occurred_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    conversation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(32))
    manual_send_receipt_id: Mapped[int | None] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
