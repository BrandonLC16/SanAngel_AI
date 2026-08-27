import asyncio
import hashlib
import hmac
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI, Request

from backend.app.api.dependencies import get_message_orchestrator_factory
from backend.app.core.config import HttpSettings, Settings, get_settings
from backend.app.core.exceptions import AIProviderRateLimitError
from backend.app.core.logging import HTTP_LOGGER_NAME
from backend.app.main import create_app
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.idempotency_store import InMemoryIdempotencyStore
from backend.app.services.message_orchestrator import MessageOrchestrator

WEBHOOK_PATH = "/api/v1/whatsapp/webhook"


class RecordingMessageOrchestrator:
    def __init__(self) -> None:
        self.messages: list[InboundMessage] = []

    async def process_message(self, message: InboundMessage) -> None:
        self.messages.append(message)


class FakeChatResponder:
    def __init__(self, *, answer: str, error: Exception | None = None) -> None:
        self._answer = answer
        self.error = error
        self.messages: list[str] = []

    async def answer(self, message: str) -> str:
        self.messages.append(message)
        if self.error is not None:
            raise self.error
        return self._answer


class FakeWhatsAppSender:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, bool]] = []

    async def send_text(
        self,
        recipient: str,
        text: str,
        *,
        preview_url: bool = False,
    ) -> str:
        self.calls.append((recipient, text, preview_url))
        return "wamid.test-only-outbound-message-id"


def make_application(
    verify_token: str | None = "test-only-verify-token-marker",
    app_secret: str | None = "test-only-meta-app-secret-marker",
    orchestrator: MessageOrchestrator | RecordingMessageOrchestrator | None = None,
) -> FastAPI:
    application = create_app(HttpSettings(app_env="testing", log_level="INFO", _env_file=None))
    settings = Settings(
        openai_api_key="test-only-openai-credential-placeholder",
        whatsapp_verify_token=verify_token,
        meta_app_secret=app_secret,
        _env_file=None,
    )
    application.dependency_overrides[get_settings] = lambda: settings

    selected_orchestrator = orchestrator or RecordingMessageOrchestrator()

    @asynccontextmanager
    async def use_test_orchestrator(_settings: Settings) -> AsyncIterator[object]:
        yield selected_orchestrator

    application.dependency_overrides[get_message_orchestrator_factory] = lambda: (
        use_test_orchestrator
    )
    return application


async def send_handshake(
    application: FastAPI,
    params: list[tuple[str, str]],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.get(WEBHOOK_PATH, params=params)


def valid_params(verify_token: str, challenge: str = "1158201444") -> list[tuple[str, str]]:
    return [
        ("hub.mode", "subscribe"),
        ("hub.verify_token", verify_token),
        ("hub.challenge", challenge),
    ]


def sign_payload(app_secret: str, raw_body: bytes) -> str:
    digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


def text_message_payload(
    sender: str,
    text: str,
    *,
    message_id: str = "wamid.test-only-inbound-message-id",
) -> bytes:
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": sender,
                                    "id": message_id,
                                    "timestamp": "1720000000",
                                    "type": "text",
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ]
            }
        ],
    }
    return json.dumps(payload, separators=(",", ":")).encode()


async def send_webhook(
    application: FastAPI,
    raw_body: bytes,
    headers: list[tuple[str, str]],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://testserver",
    ) as client:
        return await client.post(WEBHOOK_PATH, content=raw_body, headers=headers)


def test_valid_handshake_returns_only_challenge_and_does_not_log_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    verify_token = "test-only-verify-token-marker"
    challenge = "1158201444"
    application = make_application(verify_token)

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(send_handshake(application, valid_params(verify_token, challenge)))

    assert response.status_code == 200
    assert response.content == challenge.encode("ascii")
    assert response.headers["content-type"].startswith("text/plain")
    assert verify_token not in caplog.text
    assert challenge not in caplog.text


def test_incorrect_verify_token_is_rejected_without_reflection_or_logging(
    caplog: pytest.LogCaptureFixture,
) -> None:
    configured_token = "test-only-configured-token-marker"
    incorrect_token = "test-only-incorrect-token-marker"
    application = make_application(configured_token)

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(send_handshake(application, valid_params(incorrect_token)))

    assert response.status_code == 403
    assert response.content == b""
    assert configured_token not in response.text
    assert incorrect_token not in response.text
    assert configured_token not in caplog.text
    assert incorrect_token not in caplog.text


@pytest.mark.parametrize(
    "params",
    (
        [
            ("hub.mode", "unsubscribe"),
            ("hub.verify_token", "test-only-verify-token-marker"),
            ("hub.challenge", "1158201444"),
        ],
        [
            ("hub.mode", "subscribe"),
            ("hub.verify_token", "test-only-verify-token-marker"),
            ("hub.challenge", "not-an-integer"),
        ],
        [
            ("hub.mode", "subscribe"),
            ("hub.verify_token", "test-only-verify-token-marker"),
        ],
        [
            ("hub.mode", "subscribe"),
            ("hub.verify_token", "test-only-verify-token-marker"),
            ("hub.challenge", "1158201444"),
            ("hub.challenge", "1158201445"),
        ],
    ),
)
def test_invalid_mode_or_challenge_is_rejected(params: list[tuple[str, str]]) -> None:
    application = make_application("test-only-verify-token-marker")

    response = asyncio.run(send_handshake(application, params))

    assert response.status_code == 403
    assert response.content == b""


def test_missing_verify_token_configuration_fails_closed() -> None:
    application = make_application(verify_token=None)

    response = asyncio.run(
        send_handshake(application, valid_params("test-only-verify-token-marker"))
    )

    assert response.status_code == 503
    assert response.content == b""


def test_valid_post_signature_over_exact_raw_body_is_accepted() -> None:
    app_secret = "test-only-meta-app-secret-marker"
    raw_body = b'{"object":"whatsapp_business_account","entry":[]}'
    application = make_application(app_secret=app_secret)
    signature = sign_payload(app_secret, raw_body)

    response = asyncio.run(
        send_webhook(application, raw_body, [("X-Hub-Signature-256", signature)])
    )

    assert response.status_code == 200
    assert response.content == b""


def test_authenticated_text_message_completes_chat_and_outbound_flow_with_mocks() -> None:
    app_secret = "test-only-meta-app-secret-marker"
    sender = "5215550000001"
    inbound_text = "test-only-private-inbound-text-marker"
    answer = "test-only-private-answer-marker"
    chat_service = FakeChatResponder(answer=answer)
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    application = make_application(app_secret=app_secret, orchestrator=orchestrator)
    raw_body = text_message_payload(sender, f"  {inbound_text}  ")

    response = asyncio.run(
        send_webhook(
            application,
            raw_body,
            [("X-Hub-Signature-256", sign_payload(app_secret, raw_body))],
        )
    )

    assert response.status_code == 200
    assert response.content == b""
    assert chat_service.messages == [inbound_text]
    assert whatsapp_client.calls == [(sender, answer, False)]


def test_duplicate_authenticated_message_id_is_acked_without_a_second_response() -> None:
    app_secret = "test-only-meta-app-secret-marker"
    sender = "5215550000001"
    inbound_text = "test-only-duplicate-inbound-text-marker"
    answer = "test-only-single-answer-marker"
    chat_service = FakeChatResponder(answer=answer)
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    application = make_application(app_secret=app_secret, orchestrator=orchestrator)
    raw_body = text_message_payload(sender, inbound_text)
    headers = [("X-Hub-Signature-256", sign_payload(app_secret, raw_body))]

    async def send_twice() -> tuple[httpx.Response, httpx.Response]:
        first = await send_webhook(application, raw_body, headers)
        second = await send_webhook(application, raw_body, headers)
        return first, second

    first_response, duplicate_response = asyncio.run(send_twice())

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert first_response.content == duplicate_response.content == b""
    assert chat_service.messages == [inbound_text]
    assert whatsapp_client.calls == [(sender, answer, False)]


def test_chat_failure_returns_safe_error_without_sending_or_leaking_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app_secret = "test-only-meta-app-secret-marker"
    sender = "5215550000001"
    inbound_text = "test-only-private-inbound-text-marker"
    answer = "test-only-private-answer-marker"
    internal_detail = "test-only-private-provider-failure-marker"
    chat_service = FakeChatResponder(
        answer=answer,
        error=AIProviderRateLimitError(internal_detail),
    )
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    application = make_application(app_secret=app_secret, orchestrator=orchestrator)
    raw_body = text_message_payload(sender, inbound_text)

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_webhook(
                application,
                raw_body,
                [("X-Hub-Signature-256", sign_payload(app_secret, raw_body))],
            )
        )

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "message_processing_failed",
        "message": "No fue posible procesar el mensaje recibido.",
    }
    assert whatsapp_client.calls == []
    rendered = f"{response.text}\n{caplog.text}"
    assert sender not in rendered
    assert inbound_text not in rendered
    assert answer not in rendered
    assert internal_detail not in rendered


def test_signature_is_checked_against_untouched_raw_body() -> None:
    app_secret = "test-only-meta-app-secret-marker"
    signed_body = b'{"object":"whatsapp_business_account","entry":[]}'
    changed_body = b'{ "object": "whatsapp_business_account", "entry": [] }'
    application = make_application(app_secret=app_secret)
    signature = sign_payload(app_secret, signed_body)

    response = asyncio.run(
        send_webhook(application, changed_body, [("X-Hub-Signature-256", signature)])
    )

    assert response.status_code == 403
    assert response.content == b""


def test_unauthenticated_payload_is_rejected_before_json_is_accessed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    json_was_accessed = False

    async def track_json_access(request: Request) -> object:
        nonlocal json_was_accessed
        json_was_accessed = True
        return {}

    monkeypatch.setattr(Request, "json", track_json_access)
    application = make_application()

    response = asyncio.run(
        send_webhook(
            application,
            b'{"untrusted":"payload"}',
            [("X-Hub-Signature-256", "sha256=" + "0" * 64)],
        )
    )

    assert response.status_code == 403
    assert response.content == b""
    assert json_was_accessed is False


def test_unauthenticated_text_does_not_build_provider_adapters() -> None:
    application = make_application()
    application.dependency_overrides.pop(get_message_orchestrator_factory)
    raw_body = text_message_payload("5215550000001", "texto no autenticado")

    response = asyncio.run(
        send_webhook(
            application,
            raw_body,
            [("X-Hub-Signature-256", "sha256=" + "0" * 64)],
        )
    )

    assert response.status_code == 403
    assert response.content == b""


@pytest.mark.parametrize(
    "headers",
    (
        [],
        [("X-Hub-Signature-256", "sha1=" + "0" * 64)],
        [("X-Hub-Signature-256", "sha256=not-hex")],
        [("X-Hub-Signature-256", "sha256=" + "0" * 63)],
        [
            ("X-Hub-Signature-256", "sha256=" + "0" * 64),
            ("X-Hub-Signature-256", "sha256=" + "1" * 64),
        ],
    ),
)
def test_missing_or_malformed_post_signature_is_rejected(
    headers: list[tuple[str, str]],
) -> None:
    application = make_application()

    response = asyncio.run(send_webhook(application, b"{}", headers))

    assert response.status_code == 403
    assert response.content == b""


def test_invalid_signature_does_not_expose_or_log_secret_body_or_header(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app_secret = "test-only-meta-app-secret-marker"
    body_marker = "test-only-private-body-marker"
    invalid_signature = "sha256=" + "0" * 64
    application = make_application(app_secret=app_secret)

    with caplog.at_level(logging.WARNING, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_webhook(
                application,
                body_marker.encode("utf-8"),
                [("X-Hub-Signature-256", invalid_signature)],
            )
        )

    assert response.status_code == 403
    assert response.content == b""
    assert app_secret not in caplog.text
    assert body_marker not in caplog.text
    assert invalid_signature not in caplog.text


def test_missing_meta_app_secret_fails_closed() -> None:
    application = make_application(app_secret=None)

    response = asyncio.run(send_webhook(application, b"{}", []))

    assert response.status_code == 503
    assert response.content == b""


@pytest.mark.parametrize(
    "raw_body",
    (
        b"not-json",
        b"[]",
        b'{"object":"whatsapp_business_account","entry":"unexpected"}',
    ),
)
def test_authenticated_unusual_payload_does_not_break_webhook(raw_body: bytes) -> None:
    app_secret = "test-only-meta-app-secret-marker"
    application = make_application(app_secret=app_secret)
    signature = sign_payload(app_secret, raw_body)

    response = asyncio.run(
        send_webhook(application, raw_body, [("X-Hub-Signature-256", signature)])
    )

    assert response.status_code == 200
    assert response.content == b""


def test_authenticated_payload_body_is_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    app_secret = "test-only-meta-app-secret-marker"
    body_marker = "test-only-private-text-body-marker"
    raw_body = (
        '{"object":"whatsapp_business_account","entry":[{"changes":[{"field":"messages",'
        '"value":{"messaging_product":"whatsapp","messages":[{"from":"5215550000001",'
        '"id":"wamid.test-only-id","type":"text","text":{"body":"'
        f"{body_marker}"
        '"}}]}}]}]}'
    ).encode()
    application = make_application(app_secret=app_secret)
    signature = sign_payload(app_secret, raw_body)

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_webhook(application, raw_body, [("X-Hub-Signature-256", signature)])
        )

    assert response.status_code == 200
    assert body_marker not in caplog.text
    assert raw_body.decode() not in caplog.text
