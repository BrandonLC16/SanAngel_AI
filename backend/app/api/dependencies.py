from functools import lru_cache

from backend.app.core.config import get_settings
from backend.app.services.chat_service import ChatService
from backend.app.services.openai_service import OpenAIService


@lru_cache
def get_chat_service() -> ChatService:
    """Build the application service lazily so health does not require provider credentials."""

    settings = get_settings()
    return ChatService(
        OpenAIService(settings),
        max_message_chars=settings.chat_max_message_chars,
    )
