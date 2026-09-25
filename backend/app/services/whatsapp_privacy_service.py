"""Branch-scoped retention and erasure for minimal WhatsApp metadata."""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, exists, func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import AssistantSettings, ConversationIdentitySettings
from backend.app.core.exceptions import BranchNotConfiguredError, ServiceUnavailableError
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.message import Message
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.branch_scope import BranchScope
from backend.app.services.conversation_identity_service import ConversationIdentityService

CONVERSATION_RETENTION_DAYS = 30
MESSAGE_RETENTION_DAYS = 30
COMPLETED_RECEIPT_RETENTION_DAYS = 30
CLAIM_REVIEW_AFTER_DAYS = 1
UNRESOLVED_QUESTION_RETENTION_DAYS = 30

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class PurgeResult:
    conversations: int
    messages: int
    completed_receipts: int
    claimed_for_review: int
    unresolved_questions: int = 0


class WhatsAppPrivacyService:
    """Preview/purge expired metadata; never auto-delete unresolved receipts."""

    def __init__(
        self, session_factory: sessionmaker[Session], *, settings: AssistantSettings
    ) -> None:
        self._session_factory = session_factory
        self._identity_settings = (
            settings if isinstance(settings, ConversationIdentitySettings) else None
        )
        self._scope = BranchScope.from_settings(settings)

    def purge_expired(self, *, apply: bool = False, now: datetime | None = None) -> PurgeResult:
        instant = self._validated_now(now)
        conversation_cutoff = instant - timedelta(days=CONVERSATION_RETENTION_DAYS)
        message_cutoff = instant - timedelta(days=MESSAGE_RETENTION_DAYS)
        receipt_cutoff = instant - timedelta(days=COMPLETED_RECEIPT_RETENTION_DAYS)
        review_cutoff = instant - timedelta(days=CLAIM_REVIEW_AFTER_DAYS)
        unresolved_cutoff = instant - timedelta(days=UNRESOLVED_QUESTION_RETENTION_DAYS)
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                old_messages = (
                    Message.branch_id == branch_id,
                    Message.occurred_at < message_cutoff,
                )
                old_conversations = (
                    Conversation.branch_id == branch_id,
                    Conversation.updated_at < conversation_cutoff,
                    ~exists(
                        select(Message.id).where(
                            Message.branch_id == branch_id,
                            Message.conversation_id == Conversation.id,
                            Message.occurred_at >= message_cutoff,
                        )
                    ),
                )
                old_receipts = (
                    WhatsAppEventReceipt.branch_id == branch_id,
                    WhatsAppEventReceipt.status == "completed",
                    WhatsAppEventReceipt.completed_at < receipt_cutoff,
                )
                old_unresolved = (
                    UnresolvedQuestion.branch_id == branch_id,
                    UnresolvedQuestion.last_seen_at < unresolved_cutoff,
                )
                claimed_for_review = session.scalar(
                    select(func.count())
                    .select_from(WhatsAppEventReceipt)
                    .where(
                        WhatsAppEventReceipt.branch_id == branch_id,
                        WhatsAppEventReceipt.status == "claimed",
                        WhatsAppEventReceipt.received_at < review_cutoff,
                    )
                )
                if apply:
                    messages = session.execute(delete(Message).where(*old_messages)).rowcount
                    session.execute(
                        delete(ConversationResponderState).where(
                            ConversationResponderState.branch_id == branch_id,
                            ConversationResponderState.conversation_id.in_(
                                select(Conversation.id).where(*old_conversations)
                            ),
                        )
                    )
                    conversations = session.execute(
                        delete(Conversation).where(*old_conversations)
                    ).rowcount
                    completed_receipts = session.execute(
                        delete(WhatsAppEventReceipt).where(*old_receipts)
                    ).rowcount
                    unresolved_questions = session.execute(
                        delete(UnresolvedQuestion).where(*old_unresolved)
                    ).rowcount
                else:
                    messages = session.scalar(
                        select(func.count()).select_from(Message).where(*old_messages)
                    )
                    conversations = session.scalar(
                        select(func.count()).select_from(Conversation).where(*old_conversations)
                    )
                    completed_receipts = session.scalar(
                        select(func.count()).select_from(WhatsAppEventReceipt).where(*old_receipts)
                    )
                    unresolved_questions = session.scalar(
                        select(func.count()).select_from(UnresolvedQuestion).where(*old_unresolved)
                    )
        except SQLAlchemyError:
            raise ServiceUnavailableError("WhatsApp metadata purge failed") from None
        result = PurgeResult(
            conversations or 0,
            messages or 0,
            completed_receipts or 0,
            claimed_for_review or 0,
            unresolved_questions or 0,
        )
        logger.info(
            "whatsapp_metadata_purge branch_code=%s applied=%s conversations=%d messages=%d "
            "completed_receipts=%d claimed_for_review=%d unresolved_questions=%d",
            self._scope.branch_code,
            apply,
            result.conversations,
            result.messages,
            result.completed_receipts,
            result.claimed_for_review,
            result.unresolved_questions,
        )
        return result

    def erase_sender(self, external_user_id: str) -> bool:
        """Erase one scoped conversation and its message metadata using a known sender ID."""

        if self._identity_settings is None:
            raise ServiceUnavailableError("conversation identity key is not configured")
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                external_user_key = ConversationIdentityService(
                    session, settings=self._identity_settings
                ).external_user_key(external_user_id)
                conversation_id = session.scalar(
                    select(Conversation.id).where(
                        Conversation.branch_id == branch_id,
                        Conversation.channel == "whatsapp",
                        Conversation.external_user_key == external_user_key,
                    )
                )
                if conversation_id is None:
                    return False
                session.execute(
                    delete(Message).where(
                        Message.branch_id == branch_id,
                        Message.conversation_id == conversation_id,
                    )
                )
                session.execute(
                    delete(ConversationResponderState).where(
                        ConversationResponderState.branch_id == branch_id,
                        ConversationResponderState.conversation_id == conversation_id,
                    )
                )
                session.execute(
                    delete(Conversation).where(
                        Conversation.id == conversation_id,
                        Conversation.branch_id == branch_id,
                    )
                )
        except SQLAlchemyError:
            raise ServiceUnavailableError("WhatsApp conversation erasure failed") from None
        logger.info("whatsapp_conversation_erased branch_code=%s", self._scope.branch_code)
        return True

    def _branch_id(self, session: Session) -> int:
        branch = BranchRepository(session).get_by_code(self._scope.branch_code)
        if branch is None:
            raise BranchNotConfiguredError("assistant branch is missing")
        return branch.id

    @staticmethod
    def _validated_now(now: datetime | None) -> datetime:
        if now is None:
            return datetime.now(UTC)
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise ValueError("now must be a timezone-aware datetime")
        return now.astimezone(UTC)
