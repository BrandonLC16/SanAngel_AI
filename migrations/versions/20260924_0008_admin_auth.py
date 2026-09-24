"""Create branch-scoped admin credentials, sessions, and login throttles.

Revision ID: 20260924_0008
Revises: 20260924_0007
Create Date: 2026-09-24
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260924_0008"
down_revision: str | Sequence[str] | None = "20260924_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="1", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "length(username) BETWEEN 3 AND 64", name="ck_admin_users_username_length"
        ),
        sa.CheckConstraint("password_hash LIKE '$argon2id$%'", name="ck_admin_users_argon2id"),
        sa.ForeignKeyConstraint(
            ["branch_id"], ["branches.id"], name="fk_admin_users_branch", ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_users"),
        sa.UniqueConstraint("branch_id", "username", name="uq_admin_users_branch_username"),
        sa.UniqueConstraint("id", "branch_id", name="uq_admin_users_id_branch"),
    )
    op.create_table(
        "admin_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "length(token_hash) = 64 AND token_hash NOT GLOB '*[^0-9a-f]*'",
            name="ck_admin_sessions_token_hash",
        ),
        sa.ForeignKeyConstraint(
            ["user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_sessions_user_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_sessions"),
        sa.UniqueConstraint("token_hash", name="uq_admin_sessions_token_hash"),
    )
    op.create_index("ix_admin_sessions_branch_user", "admin_sessions", ["branch_id", "user_id"])
    op.create_table(
        "admin_login_throttles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("branch_id", sa.Integer(), nullable=False),
        sa.Column("bucket_key", sa.String(length=64), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "length(bucket_key) = 64 AND bucket_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_admin_login_throttles_key",
        ),
        sa.CheckConstraint("attempts > 0", name="ck_admin_login_throttles_attempts"),
        sa.ForeignKeyConstraint(
            ["branch_id"],
            ["branches.id"],
            name="fk_admin_login_throttles_branch",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_admin_login_throttles"),
        sa.UniqueConstraint("branch_id", "bucket_key", name="uq_admin_login_throttles_branch_key"),
    )
    op.create_index(
        "ix_admin_login_throttles_window", "admin_login_throttles", ["window_started_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_admin_login_throttles_window", table_name="admin_login_throttles")
    op.drop_table("admin_login_throttles")
    op.drop_index("ix_admin_sessions_branch_user", table_name="admin_sessions")
    op.drop_table("admin_sessions")
    op.drop_table("admin_users")
