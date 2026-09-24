"""Branch-scoped administrator credentials; only an Argon2id hash is stored."""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AdminUser(Base):
    __tablename__ = "admin_users"
    __table_args__ = (
        CheckConstraint("length(username) BETWEEN 3 AND 64", name="ck_admin_users_username_length"),
        CheckConstraint("password_hash LIKE '$argon2id$%'", name="ck_admin_users_argon2id"),
        UniqueConstraint("branch_id", "username", name="uq_admin_users_branch_username"),
        UniqueConstraint("id", "branch_id", name="uq_admin_users_id_branch"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    username: Mapped[str] = mapped_column(String(64), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="1"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    __table_args__ = (
        CheckConstraint(
            "length(token_hash) = 64 AND token_hash NOT GLOB '*[^0-9a-f]*'",
            name="ck_admin_sessions_token_hash",
        ),
        ForeignKeyConstraint(
            ["user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_sessions_user_branch",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("token_hash", name="uq_admin_sessions_token_hash"),
        Index("ix_admin_sessions_branch_user", "branch_id", "user_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class AdminLoginThrottle(Base):
    __tablename__ = "admin_login_throttles"
    __table_args__ = (
        CheckConstraint(
            "length(bucket_key) = 64 AND bucket_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_admin_login_throttles_key",
        ),
        CheckConstraint("attempts > 0", name="ck_admin_login_throttles_attempts"),
        UniqueConstraint("branch_id", "bucket_key", name="uq_admin_login_throttles_branch_key"),
        Index("ix_admin_login_throttles_window", "window_started_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    bucket_key: Mapped[str] = mapped_column(String(64), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False)
    window_started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
