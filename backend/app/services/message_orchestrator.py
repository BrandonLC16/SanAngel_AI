from typing import Protocol

from backend.app.core.exceptions import ApplicationError, MessageProcessingError
from backend.app.schemas.whatsapp import InboundMessage


class ChatResponder(Protocol):
    async def answer(self, message: str) -> str: ...


class WhatsAppTextSender(Protocol):
    async def send_text(
        self,
        recipient: str,
        text: str,
        *,
        preview_url: bool = False,
    ) -> str: ...


class MessageOrchestrator:
    """Coordinate one normalized inbound message without provider-specific logic."""

    def __init__(self, chat_service: ChatResponder, whatsapp_client: WhatsAppTextSender) -> None:
        self._chat_service = chat_service
        self._whatsapp_client = whatsapp_client

    async def process_message(self, message: InboundMessage) -> None:
        try:
            answer = await self._chat_service.answer(message.text)
            await self._whatsapp_client.send_text(message.sender_id, answer)
        except ApplicationError:
            raise MessageProcessingError("inbound message flow failed") from None
