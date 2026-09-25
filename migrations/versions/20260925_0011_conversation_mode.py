"""Persist exclusive AI or assigned human response mode.

Revision ID: 20260925_0011
Revises: 20260924_0010
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260925_0011"
down_revision: str | Sequence[str] | None = "20260924_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_responder_states",
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=8), server_default="AI", nullable=False),
        sa.Column("assigned_admin_user_id", sa.Integer(), nullable=True),
        sa.Column("ai_reply_count", sa.Integer(), server_default="0", nullable=False),
        sa.CheckConstraint("mode IN ('AI', 'HUMAN')", name="ck_conversation_responder_mode"),
        sa.CheckConstraint("ai_reply_count >= 0", name="ck_conversation_responder_ai_reply_count"),
        sa.CheckConstraint(
            "(mode = 'AI' AND assigned_admin_user_id IS NULL) OR "
            "(mode = 'HUMAN' AND assigned_admin_user_id IS NOT NULL AND ai_reply_count = 0)",
            name="ck_conversation_responder_owner",
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_conversation_responder_conversation_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_admin_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_conversation_responder_admin_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("conversation_id"),
    )
    op.execute(
        sa.text(
            "INSERT INTO conversation_responder_states "
            "(conversation_id, branch_id, mode, ai_reply_count) "
            "SELECT id, branch_id, 'AI', 0 FROM conversations"
        )
    )


def downgrade() -> None:
    op.drop_table("conversation_responder_states")
