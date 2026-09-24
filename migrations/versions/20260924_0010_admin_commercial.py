"""Add managed FAQ and minimal transactional commercial auditing.

Revision ID: 20260924_0010
Revises: 20260924_0009
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0010"
down_revision: str | Sequence[str] | None = "20260924_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "managed_faqs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(length=16), nullable=False),
        sa.Column("question", sa.String(length=240), nullable=False),
        sa.Column("question_key", sa.String(length=240), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
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
        sa.CheckConstraint(
            "category IN ('general', 'servicios', 'pagos', 'entregas', 'politicas')",
            name="ck_managed_faqs_category",
        ),
        sa.CheckConstraint("length(question) BETWEEN 1 AND 240", name="ck_managed_faqs_question"),
        sa.CheckConstraint("length(answer) BETWEEN 1 AND 1200", name="ck_managed_faqs_answer"),
        sa.CheckConstraint(
            "length(question_key) BETWEEN 1 AND 240", name="ck_managed_faqs_question_key"
        ),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "question_key", name="uq_managed_faqs_branch_question"),
    )
    op.create_index("ix_managed_faqs_branch_active", "managed_faqs", ["branch_id", "is_active"])
    op.create_table(
        "admin_commercial_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("resource", sa.String(length=16), nullable=False),
        sa.Column("resource_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(length=24), nullable=True),
        sa.Column("old_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("new_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "resource IN ('branch', 'product', 'price', 'faq')",
            name="ck_admin_commercial_audits_resource",
        ),
        sa.CheckConstraint(
            "action IN ('create', 'update', 'deactivate', 'delete')",
            name="ck_admin_commercial_audits_action",
        ),
        sa.CheckConstraint(
            "resource != 'price' OR (product_id IS NOT NULL AND unit IS NOT NULL)",
            name="ck_admin_commercial_audits_price_context",
        ),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_commercial_audits_actor_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id", "branch_id"],
            ["products.id", "products.branch_id"],
            name="fk_admin_commercial_audits_product_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_admin_commercial_audits_branch_time",
        "admin_commercial_audits",
        ["branch_id", "changed_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_admin_commercial_audits_branch_time", table_name="admin_commercial_audits")
    op.drop_table("admin_commercial_audits")
    op.drop_index("ix_managed_faqs_branch_active", table_name="managed_faqs")
    op.drop_table("managed_faqs")
