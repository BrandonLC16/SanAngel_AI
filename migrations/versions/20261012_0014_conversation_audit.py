"""Add short-lived human conversation audit events.

Revision ID: 20261012_0014
Revises: 20261012_0013
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261012_0014"
down_revision: str | Sequence[str] | None = "20261012_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversation_audits",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer()),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("reason", sa.String(32)),
        sa.Column("manual_send_receipt_id", sa.Integer()),
        sa.Column(
            "occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
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
        sa.ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_conversation_audits_conversation_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_conversation_audits_actor_branch",
            ondelete="RESTRICT",
        ),
    )
    op.create_index(
        "ix_conversation_audits_branch_time", "conversation_audits", ["branch_id", "occurred_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_audits_branch_time", table_name="conversation_audits")
    op.drop_table("conversation_audits")
