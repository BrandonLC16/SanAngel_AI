"""Create exact branch-scoped product prices.

Revision ID: 20260922_0004
Revises: 20260922_0003
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0004"
down_revision: str | Sequence[str] | None = "20260922_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("products") as batch_op:
        batch_op.create_unique_constraint(
            "uq_products_id_branch_id",
            ["id", "branch_id"],
        )

    op.create_table(
        "prices",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("unit", sa.String(length=24), nullable=False),
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
        sa.CheckConstraint("amount >= 0", name="ck_prices_amount_non_negative"),
        sa.CheckConstraint(
            "amount <= 9999999999.99",
            name="ck_prices_amount_maximum",
        ),
        sa.CheckConstraint(
            "round(amount, 2) = amount",
            name="ck_prices_amount_scale",
        ),
        sa.CheckConstraint(
            "length(unit) BETWEEN 1 AND 24",
            name="ck_prices_unit_length",
        ),
        sa.CheckConstraint("unit = lower(unit)", name="ck_prices_unit_lowercase"),
        sa.CheckConstraint(
            "unit NOT GLOB '*[^a-z0-9-]*'",
            name="ck_prices_unit_characters",
        ),
        sa.CheckConstraint(
            "substr(unit, 1, 1) GLOB '[a-z]'",
            name="ck_prices_unit_prefix",
        ),
        sa.CheckConstraint("substr(unit, -1, 1) <> '-'", name="ck_prices_unit_suffix"),
        sa.CheckConstraint("instr(unit, '--') = 0", name="ck_prices_unit_hyphens"),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_prices_branch_id_branches",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["product_id", "branch_id"],
            ["products.id", "products.branch_id"],
            name="fk_prices_product_id_branch_id_products",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_prices"),
        sa.UniqueConstraint(
            "branch_id",
            "product_id",
            "unit",
            name="uq_prices_branch_id_product_id_unit",
        ),
    )


def downgrade() -> None:
    op.drop_table("prices")

    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint("uq_products_id_branch_id", type_="unique")
