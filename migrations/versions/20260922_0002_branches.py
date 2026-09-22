"""Create branch profiles.

Revision ID: 20260922_0002
Revises: 20260921_0001
Create Date: 2026-09-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260922_0002"
down_revision: str | Sequence[str] | None = "20260921_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "branches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=48), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("address", sa.String(length=300), nullable=False),
        sa.Column("phone", sa.String(length=16), nullable=True),
        sa.Column("business_hours", sa.Text(), nullable=False),
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
        sa.CheckConstraint("length(code) BETWEEN 2 AND 48", name="ck_branches_code_length"),
        sa.CheckConstraint("code = lower(code)", name="ck_branches_code_lowercase"),
        sa.CheckConstraint(
            "code NOT GLOB '*[^a-z0-9-]*'",
            name="ck_branches_code_characters",
        ),
        sa.CheckConstraint(
            "substr(code, 1, 1) GLOB '[a-z]'",
            name="ck_branches_code_prefix",
        ),
        sa.CheckConstraint("substr(code, -1, 1) <> '-'", name="ck_branches_code_suffix"),
        sa.CheckConstraint("instr(code, '--') = 0", name="ck_branches_code_hyphens"),
        sa.CheckConstraint(
            "length(trim(name)) BETWEEN 1 AND 120",
            name="ck_branches_name_length",
        ),
        sa.CheckConstraint(
            "length(trim(address)) BETWEEN 1 AND 300",
            name="ck_branches_address_length",
        ),
        sa.CheckConstraint(
            "phone IS NULL OR (length(phone) BETWEEN 9 AND 16 AND phone = trim(phone))",
            name="ck_branches_phone_length",
        ),
        sa.CheckConstraint(
            "length(trim(business_hours)) BETWEEN 1 AND 500",
            name="ck_branches_business_hours_length",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_branches"),
        sa.UniqueConstraint("code", name="uq_branches_code"),
    )


def downgrade() -> None:
    op.drop_table("branches")
