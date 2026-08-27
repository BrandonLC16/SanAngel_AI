from typing import Protocol

from backend.app.core.exceptions import ApplicationError, MessageProcessingError
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.idempotency_store import IdempotencyStore


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

    def __init__(
        self,
        chat_service: ChatResponder,
        whatsapp_client: WhatsAppTextSender,
        idempotency_store: IdempotencyStore,
    ) -> None:
        self._chat_service = chat_service
        self._whatsapp_client = whatsapp_client
        self._idempotency_store = idempotency_store

    async def process_message(self, message: InboundMessage) -> bool:
        idempotency_key = f"{message.provider}:{message.external_message_id}"
        claimed = False
        try:
            claimed = await self._idempotency_store.claim(idempotency_key)
            if not claimed:
                return False

            answer = await self._chat_service.answer(message.text)
            await self._whatsapp_client.send_text(message.sender_id, answer)
            await self._idempotency_store.mark_processed(idempotency_key)
            return True
        except ApplicationError:
            if claimed:
                await self._idempotency_store.release(idempotency_key)
            raise MessageProcessingError("inbound message flow failed") from None
        except BaseException:
            if claimed:
                await self._idempotency_store.release(idempotency_key)
            raise
