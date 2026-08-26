import json

import pytest

from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.whatsapp_webhook_service import WhatsAppWebhookService


def encode_payload(payload: object) -> bytes:
    return json.dumps(payload, separators=(",", ":")).encode("utf-8")


def make_text_payload(
    text: object = "  Hola, quiero hacer un pedido  ",
    *,
    message_type: str = "text",
    field: str = "messages",
    messaging_product: str = "whatsapp",
) -> bytes:
    return encode_payload(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "id": "test-only-business-account-id",
                    "changes": [
                        {
                            "field": field,
                            "value": {
                                "messaging_product": messaging_product,
                                "metadata": {"phone_number_id": "100000000000001"},
                                "contacts": [{"wa_id": "5215550000001"}],
                                "messages": [
                                    {
                                        "from": "5215550000001",
                                        "id": "wamid.test-only-message-id",
                                        "timestamp": "1749416383",
                                        "type": message_type,
                                        "text": {"body": text},
                                        "provider_future_field": {"ignored": True},
                                    }
                                ],
                            },
                        }
                    ],
                }
            ],
            "provider_future_field": "ignored",
        }
    )


def test_text_message_produces_internal_inbound_message() -> None:
    service = WhatsAppWebhookService(max_text_chars=2000)

    messages = service.parse_messages(make_text_payload())

    assert messages == (
        InboundMessage(
            external_message_id="wamid.test-only-message-id",
            sender_id="5215550000001",
            text="Hola, quiero hacer un pedido",
            timestamp=1749416383,
        ),
    )


def test_status_event_is_ignored() -> None:
    service = WhatsAppWebhookService(max_text_chars=2000)
    payload = encode_payload(
        {
            "object": "whatsapp_business_account",
            "entry": [
                {
                    "changes": [
                        {
                            "field": "messages",
                            "value": {
                                "messaging_product": "whatsapp",
                                "statuses": [
                                    {
                                        "id": "wamid.test-only-status-id",
                                        "status": "delivered",
                                        "recipient_id": "5215550000001",
                                    }
                                ],
                            },
                        }
                    ]
                }
            ],
        }
    )

    assert service.parse_messages(payload) == ()


@pytest.mark.parametrize(
    ("message_type", "text"),
    (
        ("image", None),
        ("audio", None),
        ("document", None),
        ("location", None),
        ("contacts", None),
        ("interactive", None),
    ),
)
def test_unsupported_message_type_is_ignored(message_type: str, text: object) -> None:
    service = WhatsAppWebhookService(max_text_chars=2000)

    assert service.parse_messages(make_text_payload(text, message_type=message_type)) == ()


@pytest.mark.parametrize(
    "raw_body",
    (
        b"",
        b"not-json",
        b"null",
        b"[]",
        b"{}",
        b'{"object":"whatsapp_business_account","entry":"unexpected"}',
        b'{"object":"whatsapp_business_account","entry":[{"changes":[{"value":42}]}]}',
        make_text_payload(text=123),
    ),
)
def test_unusual_payload_returns_no_messages_without_raising(raw_body: bytes) -> None:
    service = WhatsAppWebhookService(max_text_chars=2000)

    assert service.parse_messages(raw_body) == ()


@pytest.mark.parametrize(
    "raw_body",
    (
        make_text_payload(field="account_update"),
        make_text_payload(messaging_product="other-provider"),
        encode_payload({"object": "other_object", "entry": []}),
    ),
)
def test_irrelevant_event_is_ignored(raw_body: bytes) -> None:
    service = WhatsAppWebhookService(max_text_chars=2000)

    assert service.parse_messages(raw_body) == ()


@pytest.mark.parametrize("text", ("", "   ", "123456"))
def test_blank_or_over_limit_text_is_ignored(text: str) -> None:
    service = WhatsAppWebhookService(max_text_chars=5)

    assert service.parse_messages(make_text_payload(text=text)) == ()


def test_text_at_configured_limit_is_accepted() -> None:
    service = WhatsAppWebhookService(max_text_chars=5)

    messages = service.parse_messages(make_text_payload(text="12345"))

    assert len(messages) == 1
    assert messages[0].text == "12345"


@pytest.mark.parametrize("max_text_chars", (0, 10_001))
def test_service_rejects_unsafe_text_limit(max_text_chars: int) -> None:
    with pytest.raises(ValueError, match="outside the supported range"):
        WhatsAppWebhookService(max_text_chars=max_text_chars)
