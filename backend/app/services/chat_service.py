from collections.abc import Awaitable
from typing import Protocol

from backend.app.core.exceptions import InvalidRequestError


class ReplyGenerator(Protocol):
    def generate_reply(self, message: str) -> Awaitable[str]: ...


class ChatService:
    """Application boundary between HTTP adapters and the reply provider."""

    def __init__(self, reply_generator: ReplyGenerator, *, max_message_chars: int) -> None:
        self._reply_generator = reply_generator
        self._max_message_chars = max_message_chars

    async def answer(self, message: str) -> str:
        normalized_message = message.strip()
        if not normalized_message or len(message) > self._max_message_chars:
            raise InvalidRequestError("chat message violates configured length limit")
        return await self._reply_generator.generate_reply(normalized_message)
