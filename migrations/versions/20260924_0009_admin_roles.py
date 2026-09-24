"""Add least-privilege roles to existing and new admin users.

Revision ID: 20260924_0009
Revises: 20260924_0008
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0009"
down_revision: str | Sequence[str] | None = "20260924_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.add_column(
            sa.Column("role", sa.String(length=16), server_default="viewer", nullable=False)
        )
        batch_op.create_check_constraint(
            "ck_admin_users_role", "role IN ('viewer', 'editor', 'owner')"
        )
    op.create_table(
        "admin_role_audits",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=False),
        sa.Column("target_user_id", sa.Integer(), nullable=False),
        sa.Column("old_role", sa.String(length=16), nullable=False),
        sa.Column("new_role", sa.String(length=16), nullable=False),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "old_role IN ('viewer', 'editor', 'owner')", name="ck_admin_role_audits_old"
        ),
        sa.CheckConstraint(
            "new_role IN ('viewer', 'editor', 'owner')", name="ck_admin_role_audits_new"
        ),
        sa.CheckConstraint("old_role != new_role", name="ck_admin_role_audits_changed"),
        sa.ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_role_audits_actor_branch",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_role_audits_target_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_role_audits"),
    )
    op.create_index(
        "ix_admin_role_audits_branch_time", "admin_role_audits", ["branch_id", "changed_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_admin_role_audits_branch_time", table_name="admin_role_audits")
    op.drop_table("admin_role_audits")
    with op.batch_alter_table("admin_users") as batch_op:
        batch_op.drop_constraint("ck_admin_users_role", type_="check")
        batch_op.drop_column("role")
