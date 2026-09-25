"""Derive conversation context only from normalized sender and installation settings."""

import asyncio
import hashlib
import hmac
import logging
import re
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import ConversationIdentitySettings
from backend.app.core.exceptions import InvalidRequestError, ServiceUnavailableError
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.repositories.conversation_repository import ConversationRepository
from backend.app.schemas.whatsapp import GREEN_API_CHAT_ID_PATTERN, InboundMessage
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.conversation_recipient_cipher import ConversationRecipientCipher

logger = logging.getLogger(__name__)
_CHAT_ID = re.compile(GREEN_API_CHAT_ID_PATTERN)


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
        self._recipient_cipher = ConversationRecipientCipher(settings)

    def resolve(self, message: InboundMessage) -> ConversationContext:
        branch = BranchService(
            BranchRepository(self._session),
            assistant_branch_code=self._scope.branch_code,
        ).get_current_branch()
        external_user_key = self.external_user_key(message.sender_id)
        conversation, created = ConversationRepository(self._session, branch=branch).get_or_create(
            external_user_key
        )
        conversation.recipient_ciphertext = self._recipient_cipher.encrypt(message.sender_id)
        logger.info(
            "conversation_context_resolved branch_code=%s status=%s",
            self._scope.branch_code,
            "created" if created else "existing",
        )
        return ConversationContext(conversation.id, branch.id, self._scope.branch_code)

    def external_user_key(self, external_user_id: str) -> str:
        """Derive the stable opaque key without persisting a caller's raw identifier."""

        if not isinstance(external_user_id, str) or _CHAT_ID.fullmatch(external_user_id) is None:
            raise InvalidRequestError("invalid WhatsApp sender id")
        return hmac.new(
            self._identity_key,
            f"whatsapp:{external_user_id}".encode(),
            hashlib.sha256,
        ).hexdigest()


class PersistentConversationContextResolver:
    """Commit conversation identity before invoking external response providers."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        settings: ConversationIdentitySettings,
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings

    async def resolve(self, message: InboundMessage) -> ConversationContext:
        return await asyncio.to_thread(self._resolve, message)

    def _resolve(self, message: InboundMessage) -> ConversationContext:
        try:
            with self._session_factory.begin() as session:
                return ConversationIdentityService(session, settings=self._settings).resolve(
                    message
                )
        except SQLAlchemyError:
            raise ServiceUnavailableError("conversation identity persistence failed") from None
