import re

from pydantic import ValidationError

from backend.app.schemas.whatsapp import (
    GREEN_API_CHAT_ID_PATTERN,
    MAX_WHATSAPP_TEXT_CHARS,
    GreenAPIMessageData,
    GreenAPIWebhookPayload,
    InboundMessage,
)

_GREEN_API_CHAT_ID = re.compile(GREEN_API_CHAT_ID_PATTERN)
_SUPPORTED_TEXT_TYPES = {"textMessage", "extendedTextMessage", "quotedMessage"}


class WhatsAppWebhookService:
    """Validate authenticated GREEN-API payloads and normalize supported text messages."""

    def __init__(self, *, max_text_chars: int, expected_instance_id: str) -> None:
        if not 1 <= max_text_chars <= MAX_WHATSAPP_TEXT_CHARS:
            raise ValueError("max_text_chars is outside the supported range")
        if re.fullmatch(r"[1-9][0-9]{0,19}", expected_instance_id) is None:
            raise ValueError("expected_instance_id has an invalid format")
        self._max_text_chars = max_text_chars
        self._expected_instance_id = int(expected_instance_id)

    def parse_messages(self, raw_body: bytes) -> tuple[InboundMessage, ...]:
        try:
            payload = GreenAPIWebhookPayload.model_validate_json(raw_body)
        except ValidationError:
            return ()

        if (
            payload.webhook_type != "incomingMessageReceived"
            or payload.instance_data.instance_type != "whatsapp"
            or payload.instance_data.instance_id != self._expected_instance_id
            or _GREEN_API_CHAT_ID.fullmatch(payload.sender_data.chat_id) is None
        ):
            return ()

        normalized_text = self._normalize_text(payload.message_data)
        if normalized_text is None:
            return ()

        return (
            InboundMessage(
                external_message_id=payload.external_message_id,
                sender_id=payload.sender_data.chat_id,
                text=normalized_text,
                timestamp=payload.timestamp,
            ),
        )

    def _normalize_text(self, message_data: GreenAPIMessageData) -> str | None:
        if message_data.message_type not in _SUPPORTED_TEXT_TYPES:
            return None

        if message_data.message_type == "textMessage":
            text_data = message_data.text_message_data
        else:
            text_data = message_data.extended_text_message_data

        if text_data is None:
            return None

        raw_text = text_data.text
        if len(raw_text) > self._max_text_chars:
            return None

        normalized_text = raw_text.strip()
        return normalized_text or None
