"""Bind a validated FAQ source row to the installation's backend-owned branch."""

from collections.abc import Mapping
from dataclasses import dataclass

from backend.app.schemas.faq import FAQCategory, FAQSourceRow
from backend.app.services.branch_scope import BranchScope


@dataclass(frozen=True, slots=True)
class FAQRecord:
    """Validated FAQ data whose branch code came from backend configuration."""

    branch_code: str
    category: FAQCategory
    question: str
    answer: str


def validate_scoped_faq_row(values: Mapping[str, object], scope: BranchScope) -> FAQRecord:
    """Validate a row and replace its untrusted scope with the configured one."""

    row = FAQSourceRow.model_validate(values)
    if row.branch_code != scope.branch_code:
        raise ValueError("FAQ branch does not match the configured installation")
    return FAQRecord(
        branch_code=scope.branch_code,
        category=row.category,
        question=row.question,
        answer=row.answer,
    )
