"""Branch-scoped aggregate of FAQ questions without customer text."""

from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class UnresolvedQuestion(Base):
    __tablename__ = "unresolved_questions"
    __table_args__ = (
        CheckConstraint(
            "reason IN ('faq_unknown', 'faq_ambiguous')", name="ck_unresolved_questions_reason"
        ),
        CheckConstraint(
            "length(question_key) = 64 AND question_key NOT GLOB '*[^0-9a-f]*'",
            name="ck_unresolved_questions_key",
        ),
        CheckConstraint("occurrences > 0", name="ck_unresolved_questions_occurrences"),
        UniqueConstraint(
            "branch_id", "reason", "question_key", name="uq_unresolved_questions_branch_reason_key"
        ),
        Index("ix_unresolved_questions_branch_count", "branch_id", "occurrences"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    branch_id: Mapped[int] = mapped_column(
        ForeignKey("branches.id", ondelete="RESTRICT"), nullable=False
    )
    reason: Mapped[str] = mapped_column(String(24), nullable=False)
    question_key: Mapped[str] = mapped_column(String(64), nullable=False)
    occurrences: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.current_timestamp()
    )
