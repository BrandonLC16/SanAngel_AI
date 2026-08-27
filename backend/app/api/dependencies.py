from collections.abc import AsyncIterator, Callable
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from functools import lru_cache

from backend.app.core.config import Settings, get_settings
from backend.app.services.chat_service import ChatService
from backend.app.services.message_orchestrator import MessageOrchestrator
from backend.app.services.openai_service import OpenAIService
from backend.app.services.whatsapp_client import WhatsAppClient

MessageOrchestratorFactory = Callable[
    [Settings],
    AbstractAsyncContextManager[MessageOrchestrator],
]


@lru_cache
def get_chat_service() -> ChatService:
    """Build the application service lazily so health does not require provider credentials."""

    settings = get_settings()
    return ChatService(
        OpenAIService(settings),
        max_message_chars=settings.chat_max_message_chars,
    )


@asynccontextmanager
async def create_message_orchestrator(
    settings: Settings,
) -> AsyncIterator[MessageOrchestrator]:
    """Build provider adapters only after the webhook has authenticated its request."""

    async with WhatsAppClient(settings) as whatsapp_client:
        yield MessageOrchestrator(get_chat_service(), whatsapp_client)


def get_message_orchestrator_factory() -> MessageOrchestratorFactory:
    """Expose a replaceable lazy composition root for authenticated webhook processing."""

    return create_message_orchestrator
