"""Derive conversation context only from normalized sender and installation settings."""

import hashlib
import hmac
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from backend.app.core.config import ConversationIdentitySettings
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ConversationContext:
    conversation_id: int
    branch_id: int
    branch_code: str


class ConversationIdentityService:
    """Resolve a sender to a conversation without exposing its raw external ID."""

    def __init__(self, session: Session, *, settings: ConversationIdentitySettings) -> None:
        self._session = session
        self._scope = BranchScope.from_settings(settings)
        self._identity_key = settings.conversation_identity_key.get_secret_value().encode("ascii")

    def resolve(self, message: InboundMessage) -> ConversationContext:
        branch = BranchService(
            BranchRepository(self._session),
            assistant_branch_code=self._scope.branch_code,
        ).get_current_branch()
        external_user_key = hmac.new(
            self._identity_key,
            f"whatsapp:{message.sender_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        conversation, created = ConversationRepository(self._session, branch=branch).get_or_create(
            external_user_key
        )
        logger.info(
            "conversation_context_resolved branch_code=%s status=%s",
            self._scope.branch_code,
            "created" if created else "existing",
        )
        return ConversationContext(conversation.id, branch.id, self._scope.branch_code)
