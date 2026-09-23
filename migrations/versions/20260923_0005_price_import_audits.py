"""Record minimal metadata for confirmed price import attempts.

Revision ID: 20260923_0005
Revises: 20260922_0004
Create Date: 2026-09-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260923_0005"
down_revision: str | Sequence[str] | None = "20260922_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "price_import_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("attempt_id", sa.String(length=32), nullable=False),
        sa.Column("branch_code", sa.String(length=48), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("file_sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_count", sa.Integer(), nullable=False),
        sa.Column("updated_count", sa.Integer(), nullable=False),
        sa.Column("unchanged_count", sa.Integer(), nullable=False),
        sa.Column("error_count", sa.Integer(), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("errors_json", sa.Text(), nullable=False),
        sa.CheckConstraint(
            "status IN ('success', 'rejected', 'failed')",
            name="ck_price_import_audits_status",
        ),
        sa.CheckConstraint(
            "created_count >= 0 AND updated_count >= 0 AND unchanged_count >= 0 "
            "AND error_count >= 0",
            name="ck_price_import_audits_counts",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_price_import_audits"),
        sa.UniqueConstraint("attempt_id", name="uq_price_import_audits_attempt_id"),
    )
    op.create_index(
        "ix_price_import_audits_branch_time",
        "price_import_audits",
        ["branch_code", "occurred_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_price_import_audits_branch_time", table_name="price_import_audits")
    op.drop_table("price_import_audits")
