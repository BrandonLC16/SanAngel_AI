import json

import pytest

from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.whatsapp_webhook_service import WhatsAppWebhookService

INSTANCE_ID = "123456789012"
CHAT_ID = "5215550000001@c.us"


def encode_payload(payload: object) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def make_text_payload(
    text: object = "  Hola, quiero hacer un pedido  ",
    *,
    message_type: str = "textMessage",
    webhook_type: str = "incomingMessageReceived",
    instance_id: int = 123_456_789_012,
    instance_type: str = "whatsapp",
    chat_id: str = CHAT_ID,
) -> bytes:
    if message_type == "textMessage":
        message_data: dict[str, object] = {
            "typeMessage": message_type,
            "textMessageData": {"textMessage": text},
        }
    else:
        message_data = {
            "typeMessage": message_type,
            "extendedTextMessageData": {"text": text},
        }

    return encode_payload(
        {
            "typeWebhook": webhook_type,
            "instanceData": {
                "idInstance": instance_id,
                "wid": "5215559999999@c.us",
                "typeInstance": instance_type,
            },
            "timestamp": 1_749_416_383,
            "idMessage": "F7AEC1B7086ECDC7E6E45923F5EDB825",
            "senderData": {
                "chatId": chat_id,
                "sender": chat_id,
                "senderName": "Cliente",
                "providerFutureField": "ignored",
            },
            "messageData": message_data,
            "providerFutureField": "ignored",
        }
    )


def make_service(*, max_text_chars: int = 2000) -> WhatsAppWebhookService:
    return WhatsAppWebhookService(
        max_text_chars=max_text_chars,
        expected_instance_id=INSTANCE_ID,
    )


def test_text_message_produces_internal_inbound_message() -> None:
    messages = make_service().parse_messages(make_text_payload())

    assert messages == (
        InboundMessage(
            external_message_id="F7AEC1B7086ECDC7E6E45923F5EDB825",
            sender_id=CHAT_ID,
            text="Hola, quiero hacer un pedido",
            timestamp=1_749_416_383,
        ),
    )


@pytest.mark.parametrize("message_type", ("extendedTextMessage", "quotedMessage"))
def test_extended_and_quoted_text_messages_are_supported(message_type: str) -> None:
    messages = make_service().parse_messages(
        make_text_payload("Texto extendido", message_type=message_type)
    )

    assert len(messages) == 1
    assert messages[0].text == "Texto extendido"


def test_group_chat_id_is_preserved_for_reply() -> None:
    group_chat_id = "120363369140947676@g.us"

    messages = make_service().parse_messages(make_text_payload(chat_id=group_chat_id))

    assert len(messages) == 1
    assert messages[0].sender_id == group_chat_id


@pytest.mark.parametrize(
    "message_type",
    ("imageMessage", "audioMessage", "documentMessage", "locationMessage", "contactMessage"),
)
def test_unsupported_message_type_is_ignored(message_type: str) -> None:
    assert make_service().parse_messages(make_text_payload(None, message_type=message_type)) == ()


@pytest.mark.parametrize(
    "raw_body",
    (
        b"",
        b"not-json",
        b"null",
        b"[]",
        b"{}",
        b'{"typeWebhook":"incomingMessageReceived","instanceData":42}',
        make_text_payload(text=123),
    ),
)
def test_unusual_payload_returns_no_messages_without_raising(raw_body: bytes) -> None:
    assert make_service().parse_messages(raw_body) == ()


@pytest.mark.parametrize(
    "raw_body",
    (
        make_text_payload(webhook_type="outgoingMessageStatus"),
        make_text_payload(instance_id=123_456_789_013),
        make_text_payload(instance_type="telegram"),
        make_text_payload(chat_id="invalid-chat-id"),
    ),
)
def test_irrelevant_or_wrong_instance_event_is_ignored(raw_body: bytes) -> None:
    assert make_service().parse_messages(raw_body) == ()


@pytest.mark.parametrize("text", ("", "   ", "123456"))
def test_blank_or_over_limit_text_is_ignored(text: str) -> None:
    assert make_service(max_text_chars=5).parse_messages(make_text_payload(text=text)) == ()


def test_text_at_configured_limit_is_accepted() -> None:
    messages = make_service(max_text_chars=5).parse_messages(make_text_payload(text="12345"))

    assert len(messages) == 1
    assert messages[0].text == "12345"


@pytest.mark.parametrize("max_text_chars", (0, 10_001))
def test_service_rejects_unsafe_text_limit(max_text_chars: int) -> None:
    with pytest.raises(ValueError, match="outside the supported range"):
        make_service(max_text_chars=max_text_chars)


@pytest.mark.parametrize("instance_id", ("", "0", "1" * 21, "instance"))
def test_service_rejects_invalid_expected_instance_id(instance_id: str) -> None:
    with pytest.raises(ValueError, match="invalid format"):
        WhatsAppWebhookService(max_text_chars=2000, expected_instance_id=instance_id)
