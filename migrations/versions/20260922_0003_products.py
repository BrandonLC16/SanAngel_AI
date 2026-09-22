"""Create branch-scoped products.

Revision ID: 20260922_0003
Revises: 20260922_0002
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0003"
down_revision: str | Sequence[str] | None = "20260922_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
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
            "length(trim(name)) BETWEEN 1 AND 120",
            name="ck_products_name_length",
        ),
        sa.CheckConstraint(
            "length(trim(category)) BETWEEN 1 AND 80",
            name="ck_products_category_length",
        ),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_products_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_products"),
        sa.UniqueConstraint(
            "branch_id",
            "name",
            name="uq_products_branch_id_name",
        ),
    )
    op.create_index(
        "ix_products_branch_catalog",
        "products",
        ["branch_id", "is_active", "category", "name"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_products_branch_catalog", table_name="products")
    op.drop_table("products")
