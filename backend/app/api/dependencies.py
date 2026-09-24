from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from backend.app.core.config import Settings, get_conversation_identity_settings, get_settings
from backend.app.core.exceptions import BranchScopeMismatchError
from backend.app.db.session import get_database_session_factory
from backend.app.services.branch_scope import BranchScope
from backend.app.services.chat_service import ChatService
from backend.app.services.conversation_identity_service import PersistentConversationContextResolver
from backend.app.services.idempotency_store import IdempotencyStore
from backend.app.services.message_orchestrator import MessageOrchestrator
from backend.app.services.openai_service import OpenAIService
from backend.app.services.persistent_idempotency_store import PersistentIdempotencyStore
from backend.app.services.whatsapp_background_processor import (
    MessageOrchestratorFactory,
    WhatsAppBackgroundProcessor,
)
from backend.app.services.whatsapp_client import WhatsAppClient


@lru_cache
def get_chat_service() -> ChatService:
    """Build the application service lazily so health does not require provider credentials."""

    settings = get_settings()
    return ChatService(
        OpenAIService(settings),
        max_message_chars=settings.chat_max_message_chars,
    )


def get_idempotency_store(settings: Settings) -> IdempotencyStore:
    """Bind one persistent receipt store to the installation's branch."""

    return PersistentIdempotencyStore(
        get_database_session_factory(),
        branch_scope=BranchScope.from_settings(settings),
    )


@asynccontextmanager
async def create_message_orchestrator(
    settings: Settings,
) -> AsyncIterator[MessageOrchestrator]:
    """Build provider adapters only after the webhook has authenticated its request."""

    identity_settings = get_conversation_identity_settings()
    if identity_settings.assistant_branch_code != settings.assistant_branch_code:
        raise BranchScopeMismatchError("conversation identity scope does not match installation")
    conversation_context_resolver = PersistentConversationContextResolver(
        get_database_session_factory(), settings=identity_settings
    )
    async with WhatsAppClient(settings) as whatsapp_client:
        yield MessageOrchestrator(
            get_chat_service(),
            whatsapp_client,
            get_idempotency_store(settings),
            conversation_context_resolver=conversation_context_resolver,
        )


def get_message_orchestrator_factory() -> MessageOrchestratorFactory:
    """Expose a replaceable lazy composition root for authenticated webhook processing."""

    return create_message_orchestrator


def get_whatsapp_background_processor(
    orchestrator_factory: Annotated[
        MessageOrchestratorFactory,
        Depends(get_message_orchestrator_factory),
    ],
) -> WhatsAppBackgroundProcessor:
    """Compose the in-process processor while keeping provider work out of the route."""

    return WhatsAppBackgroundProcessor(orchestrator_factory)
