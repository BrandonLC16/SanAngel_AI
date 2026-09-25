"""One persistent responder state per scoped WhatsApp conversation."""

from sqlalchemy import Boolean, CheckConstraint, ForeignKeyConstraint, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.core.conversation_mode import ConversationMode
from backend.app.db.base import Base


class ConversationResponderState(Base):
    __tablename__ = "conversation_responder_states"
    __table_args__ = (
        CheckConstraint("mode IN ('AI', 'HUMAN')", name="ck_conversation_responder_mode"),
        CheckConstraint("ai_reply_count >= 0", name="ck_conversation_responder_ai_reply_count"),
        CheckConstraint(
            "(mode = 'AI' AND assigned_admin_user_id IS NULL) OR "
            "(mode = 'HUMAN' AND assigned_admin_user_id IS NOT NULL AND ai_reply_count = 0)",
            name="ck_conversation_responder_owner",
        ),
        ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_conversation_responder_conversation_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["assigned_admin_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_conversation_responder_admin_branch",
            ondelete="RESTRICT",
        ),
    )

    conversation_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    mode: Mapped[str] = mapped_column(
        String(8), nullable=False, default=ConversationMode.AI.value, server_default="AI"
    )
    assigned_admin_user_id: Mapped[int | None] = mapped_column(Integer)
    ai_reply_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    manual_send_blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
