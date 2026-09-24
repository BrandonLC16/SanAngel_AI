"""Record and query privacy-preserving unresolved FAQ aggregates."""

import hashlib
import hmac
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from backend.app.core.config import ConversationIdentitySettings
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.faq_response_policy import FAQFallback, HumanHelpReason
from backend.app.services.faq_service import MAX_FAQ_QUERY_CHARS, normalize_faq_question


@dataclass(frozen=True, slots=True)
class UnresolvedQuestionSummary:
    reason: HumanHelpReason
    question_key: str
    occurrences: int
    first_seen_at: datetime
    last_seen_at: datetime


class UnresolvedQuestionService:
    """Scope aggregates to the configured branch and never persist question text."""

    def __init__(self, session: Session, *, settings: ConversationIdentitySettings) -> None:
        self._session = session
        self._scope = BranchScope.from_settings(settings)
        self._key = settings.conversation_identity_key.get_secret_value().encode("ascii")

    def record_faq_fallback(self, query: str, fallback: FAQFallback) -> None:
        if not isinstance(fallback, FAQFallback) or fallback.human_help.reason not in {
            HumanHelpReason.FAQ_UNKNOWN,
            HumanHelpReason.FAQ_AMBIGUOUS,
        }:
            raise ValueError("an unresolved FAQ fallback is required")
        normalized = self._normalize(query)
        branch = BranchService(
            BranchRepository(self._session), assistant_branch_code=self._scope.branch_code
        ).get_current_branch()
        question_key = hmac.new(
            self._key,
            f"unresolved-faq:v1:{normalized}".encode(),
            hashlib.sha256,
        ).hexdigest()
        now = datetime.now(UTC)
        statement = insert(UnresolvedQuestion).values(
            branch_id=branch.id,
            reason=fallback.human_help.reason.value,
            question_key=question_key,
            occurrences=1,
            first_seen_at=now,
            last_seen_at=now,
        )
        self._session.execute(
            statement.on_conflict_do_update(
                index_elements=["branch_id", "reason", "question_key"],
                set_={
                    "occurrences": UnresolvedQuestion.occurrences + 1,
                    "last_seen_at": now,
                },
            )
        )

    def list_most_frequent(self, *, limit: int = 50) -> tuple[UnresolvedQuestionSummary, ...]:
        """Supply a bounded, scoped read model for an authorized future panel."""
        if type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("limit must be between 1 and 100")
        branch = BranchService(
            BranchRepository(self._session), assistant_branch_code=self._scope.branch_code
        ).get_current_branch()
        rows = self._session.scalars(
            select(UnresolvedQuestion)
            .where(UnresolvedQuestion.branch_id == branch.id)
            .order_by(UnresolvedQuestion.occurrences.desc(), UnresolvedQuestion.id)
            .limit(limit)
        ).all()
        return tuple(
            UnresolvedQuestionSummary(
                reason=HumanHelpReason(row.reason),
                question_key=row.question_key,
                occurrences=row.occurrences,
                first_seen_at=row.first_seen_at,
                last_seen_at=row.last_seen_at,
            )
            for row in rows
        )

    @staticmethod
    def _normalize(query: str) -> str:
        if not isinstance(query, str) or not 0 < len(query) <= MAX_FAQ_QUERY_CHARS:
            raise ValueError("invalid unresolved question")
        cleaned = unicodedata.normalize("NFKC", query).strip()
        if len(cleaned) > MAX_FAQ_QUERY_CHARS or not cleaned.isprintable():
            raise ValueError("invalid unresolved question")
        normalized = normalize_faq_question(cleaned)
        if not normalized or not any(character.isalnum() for character in normalized):
            raise ValueError("invalid unresolved question")
        return normalized
