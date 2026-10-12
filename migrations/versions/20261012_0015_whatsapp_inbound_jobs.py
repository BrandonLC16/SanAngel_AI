"""Persist encrypted inbound work before webhook ACK.

Revision ID: 20261012_0015
Revises: 20261012_0014
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261012_0015"
down_revision: str | Sequence[str] | None = "20261012_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "whatsapp_inbound_jobs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("provider_message_id", sa.String(512), nullable=False),
        sa.Column("sender_key", sa.String(64), nullable=False),
        sa.Column("payload_ciphertext", sa.Text(), nullable=False),
        sa.Column("status", sa.String(12), nullable=False),
        sa.Column(
            "enqueued_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("claimed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint(
            "(status = 'pending' AND claimed_at IS NULL) OR "
            "(status IN ('processing', 'uncertain') AND claimed_at IS NOT NULL)",
            name="ck_whatsapp_inbound_jobs_status",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_whatsapp_inbound_jobs_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "branch_id", "provider_message_id", name="uq_whatsapp_inbound_jobs_branch_message"
        ),
    )
    op.create_index(
        "ix_whatsapp_inbound_jobs_branch_status_time",
        "whatsapp_inbound_jobs",
        ["branch_id", "status", "enqueued_at"],
    )
    op.create_index(
        "ix_whatsapp_inbound_jobs_branch_sender",
        "whatsapp_inbound_jobs",
        ["branch_id", "sender_key"],
    )


def downgrade() -> None:
    op.drop_index("ix_whatsapp_inbound_jobs_branch_sender", table_name="whatsapp_inbound_jobs")
    op.drop_index("ix_whatsapp_inbound_jobs_branch_status_time", table_name="whatsapp_inbound_jobs")
    op.drop_table("whatsapp_inbound_jobs")
