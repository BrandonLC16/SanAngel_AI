"""Aggregate unresolved FAQ questions without storing customer text.

Revision ID: 20260924_0007
Revises: 20260924_0006
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0007"
down_revision: str | Sequence[str] | None = "20260924_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "unresolved_questions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("reason", sa.String(length=24), nullable=False),
        sa.Column("question_key", sa.String(length=64), nullable=False),
        sa.Column("occurrences", sa.Integer(), nullable=False),
        sa.Column(
            "first_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "reason IN ('faq_unknown', 'faq_ambiguous')", name="ck_unresolved_questions_reason"
        ),
        sa.CheckConstraint(
            "length(question_key) = 64 AND question_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_unresolved_questions_key",
        ),
        sa.CheckConstraint("occurrences > 0", name="ck_unresolved_questions_occurrences"),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_unresolved_questions_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_unresolved_questions"),
        sa.UniqueConstraint(
            "branch_id", "reason", "question_key", name="uq_unresolved_questions_branch_reason_key"
        ),
    )
    op.create_index(
        "ix_unresolved_questions_branch_count", "unresolved_questions", ["branch_id", "occurrences"]
    )


def downgrade() -> None:
    op.drop_index("ix_unresolved_questions_branch_count", table_name="unresolved_questions")
    op.drop_table("unresolved_questions")
