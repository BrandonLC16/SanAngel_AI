"""Managed FAQ entries and minimal transactional commercial change receipts."""

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class ManagedFAQ(Base):
    __tablename__ = "managed_faqs"
    __table_args__ = (
        CheckConstraint(
            "category IN ('general', 'servicios', 'pagos', 'entregas', 'politicas')",
            name="ck_managed_faqs_category",
        ),
        CheckConstraint("length(question) BETWEEN 1 AND 240", name="ck_managed_faqs_question"),
        CheckConstraint("length(answer) BETWEEN 1 AND 1200", name="ck_managed_faqs_answer"),
        CheckConstraint(
            "length(question_key) BETWEEN 1 AND 240", name="ck_managed_faqs_question_key"
        ),
        UniqueConstraint("branch_id", "question_key", name="uq_managed_faqs_branch_question"),
        Index("ix_managed_faqs_branch_active", "branch_id", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    category: Mapped[str] = mapped_column(String(16), nullable=False)
    question: Mapped[str] = mapped_column(String(240), nullable=False)
    question_key: Mapped[str] = mapped_column(String(240), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="1")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )


class AdminCommercialAudit(Base):
    """No request bodies, FAQ text, branch contact data, or credentials."""

    __tablename__ = "admin_commercial_audits"
    __table_args__ = (
        CheckConstraint(
            "resource IN ('branch', 'product', 'price', 'faq')",
            name="ck_admin_commercial_audits_resource",
        ),
        CheckConstraint(
            "action IN ('create', 'update', 'deactivate', 'delete')",
            name="ck_admin_commercial_audits_action",
        ),
        CheckConstraint(
            "resource != 'price' OR (product_id IS NOT NULL AND unit IS NOT NULL)",
            name="ck_admin_commercial_audits_price_context",
        ),
        ForeignKeyConstraint(
            ["actor_user_id", "branch_id"],
            ["admin_users.id", "admin_users.branch_id"],
            name="fk_admin_commercial_audits_actor_branch",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["product_id", "branch_id"],
            ["products.id", "products.branch_id"],
            name="fk_admin_commercial_audits_product_branch",
            ondelete="RESTRICT",
        ),
        Index("ix_admin_commercial_audits_branch_time", "branch_id", "changed_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(Integer, nullable=False)
    actor_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    resource: Mapped[str] = mapped_column(String(16), nullable=False)
    resource_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(16), nullable=False)
    product_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(24), nullable=True)
    old_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    new_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
