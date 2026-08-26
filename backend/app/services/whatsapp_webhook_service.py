from pydantic import ValidationError

from backend.app.schemas.whatsapp import (
    MAX_WHATSAPP_TEXT_CHARS,
    InboundMessage,
    WhatsAppMessagePayload,
    WhatsAppWebhookPayload,
)


class WhatsAppWebhookService:
    """Validate authenticated Meta payloads and normalize supported text messages."""

    def __init__(self, *, max_text_chars: int) -> None:
        if not 1 <= max_text_chars <= MAX_WHATSAPP_TEXT_CHARS:
            raise ValueError("max_text_chars is outside the supported range")
        self._max_text_chars = max_text_chars

    def parse_messages(self, raw_body: bytes) -> tuple[InboundMessage, ...]:
        try:
            payload = WhatsAppWebhookPayload.model_validate_json(raw_body)
        except ValidationError:
            return ()

        if payload.object != "whatsapp_business_account":
            return ()

        inbound_messages: list[InboundMessage] = []
        for entry in payload.entry:
            for change in entry.changes:
                value = change.value
                if (
                    change.field != "messages"
                    or value is None
                    or value.messaging_product != "whatsapp"
                ):
                    continue

                for message in value.messages:
                    normalized_message = self._normalize_text_message(message)
                    if normalized_message is not None:
                        inbound_messages.append(normalized_message)

        return tuple(inbound_messages)

    def _normalize_text_message(
        self,
        message: WhatsAppMessagePayload,
    ) -> InboundMessage | None:
        if message.message_type != "text" or message.text is None:
            return None

        raw_text = message.text.body
        if len(raw_text) > self._max_text_chars:
            return None

        normalized_text = raw_text.strip()
        if not normalized_text:
            return None

        timestamp = int(message.timestamp) if message.timestamp is not None else None
        return InboundMessage(
            external_message_id=message.external_message_id,
            sender_id=message.sender_id,
            text=normalized_text,
            timestamp=timestamp,
        )
