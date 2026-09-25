from typing import Protocol

from backend.app.core.exceptions import ApplicationError, MessageProcessingError
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.conversation_identity_service import ConversationContext
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


class ConversationContextResolver(Protocol):
    async def resolve(self, message: InboundMessage) -> ConversationContext: ...


class ConversationModeGate(Protocol):
    async def begin_ai_reply(self, conversation_id: int) -> bool: ...

    async def finish_ai_reply(self, conversation_id: int) -> None: ...


class MessageOrchestrator:
    """Coordinate one normalized inbound message without provider-specific logic."""

    def __init__(
        self,
        chat_service: ChatResponder,
        whatsapp_client: WhatsAppTextSender,
        idempotency_store: IdempotencyStore,
        *,
        conversation_context_resolver: ConversationContextResolver | None = None,
        conversation_mode_gate: ConversationModeGate | None = None,
    ) -> None:
        if (conversation_context_resolver is None) != (conversation_mode_gate is None):
            raise ValueError("conversation context and mode gate must be configured together")
        self._chat_service = chat_service
        self._whatsapp_client = whatsapp_client
        self._idempotency_store = idempotency_store
        self._conversation_context_resolver = conversation_context_resolver
        self._conversation_mode_gate = conversation_mode_gate

    async def process_message(self, message: InboundMessage) -> bool:
        idempotency_key = message.external_message_id
        claimed = False
        send_attempted = False
        ai_conversation_id: int | None = None
        try:
            claimed = await self._idempotency_store.claim(idempotency_key)
            if not claimed:
                return False

            if self._conversation_context_resolver is not None:
                context = await self._conversation_context_resolver.resolve(message)
                assert self._conversation_mode_gate is not None
                if not await self._conversation_mode_gate.begin_ai_reply(context.conversation_id):
                    await self._idempotency_store.mark_processed(idempotency_key)
                    return False
                ai_conversation_id = context.conversation_id
            answer = await self._chat_service.answer(message.text)
            send_attempted = True
            await self._whatsapp_client.send_text(message.sender_id, answer)
            await self._idempotency_store.mark_processed(idempotency_key)
            if ai_conversation_id is not None:
                assert self._conversation_mode_gate is not None
                await self._conversation_mode_gate.finish_ai_reply(ai_conversation_id)
                ai_conversation_id = None
            return True
        except ApplicationError as exc:
            if claimed and not send_attempted:
                if ai_conversation_id is not None:
                    assert self._conversation_mode_gate is not None
                    await self._conversation_mode_gate.finish_ai_reply(ai_conversation_id)
                await self._idempotency_store.release(idempotency_key)
            raise MessageProcessingError(
                "inbound message flow failed",
                source_error_code=exc.error_code,
                provider_code=getattr(exc, "provider_code", None),
                provider_subcode=getattr(exc, "provider_subcode", None),
            ) from None
        except BaseException:
            if claimed and not send_attempted:
                if ai_conversation_id is not None:
                    assert self._conversation_mode_gate is not None
                    await self._conversation_mode_gate.finish_ai_reply(ai_conversation_id)
                await self._idempotency_store.release(idempotency_key)
            raise
