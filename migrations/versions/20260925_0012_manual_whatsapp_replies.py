"""Keep encrypted recipient and minimal human send status.

Revision ID: 20260925_0012
Revises: 20260925_0011
Create Date: 2026-09-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260925_0012"
down_revision: str | Sequence[str] | None = "20260925_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("conversations", sa.Column("recipient_ciphertext", sa.String(512)))
    op.add_column(
        "conversation_responder_states",
        sa.Column("manual_send_blocked", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.create_table(
        "manual_send_receipts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("provider_message_id", sa.String(512)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'accepted', 'uncertain')", name="ck_manual_send_status"
        ),
        sa.UniqueConstraint(
            "branch_id", "conversation_id", "request_id", name="uq_manual_send_request"
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_manual_send_conversation_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_manual_send_actor_branch",
            ondelete="RESTRICT",
        ),
    )


def downgrade() -> None:
    op.drop_table("manual_send_receipts")
    op.drop_column("conversation_responder_states", "manual_send_blocked")
    op.drop_column("conversations", "recipient_ciphertext")
