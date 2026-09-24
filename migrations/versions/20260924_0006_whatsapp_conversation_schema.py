"""Create minimal WhatsApp conversation, message, and event receipt tables.

Revision ID: 20260924_0006
Revises: 20260923_0005
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0006"
down_revision: str | Sequence[str] | None = "20260923_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=16), nullable=False),
        sa.Column("external_user_key", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("channel = 'whatsapp'", name="ck_conversations_channel"),
        sa.CheckConstraint(
            "length(external_user_key) = 64 AND external_user_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_conversations_external_user_key",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_conversations_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_conversations"),
        sa.UniqueConstraint(
            "branch_id", "channel", "external_user_key", name="uq_conversations_branch_channel_user"
        ),
        sa.UniqueConstraint("id", "branch_id", name="uq_conversations_id_branch_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("conversation_id", sa.Integer(), nullable=False),
        sa.Column("direction", sa.String(length=8), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint("direction IN ('inbound', 'outbound')", name="ck_messages_direction"),
        sa.ForeignKeyConstraint(
            ["conversation_id", "branch_id"],
            ["conversations.id", "conversations.branch_id"],
            name="fk_messages_conversation_id_branch_id_conversations",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_messages"),
    )
    op.create_index(
        "ix_messages_branch_conversation_time",
        "messages",
        ["branch_id", "conversation_id", "occurred_at"],
    )

    op.create_table(
        "whatsapp_event_receipts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("provider_message_id", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(provider_message_id) BETWEEN 1 AND 512 "
            "AND provider_message_id = trim(provider_message_id)",
            name="ck_whatsapp_event_receipts_message_id",
        ),
        sa.CheckConstraint(
            "(status = 'claimed' AND completed_at IS NULL) OR "
            "(status = 'completed' AND completed_at IS NOT NULL)",
            name="ck_whatsapp_event_receipts_status",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_whatsapp_event_receipts_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_whatsapp_event_receipts"),
        sa.UniqueConstraint(
            "branch_id", "provider_message_id", name="uq_whatsapp_event_receipts_branch_message"
        ),
    )
    op.create_index(
        "ix_whatsapp_event_receipts_branch_status_time",
        "whatsapp_event_receipts",
        ["branch_id", "status", "received_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_whatsapp_event_receipts_branch_status_time", table_name="whatsapp_event_receipts"
    )
    op.drop_table("whatsapp_event_receipts")
    op.drop_index("ix_messages_branch_conversation_time", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
