import asyncio
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import BackgroundTasks, FastAPI, Request

from backend.app.api.dependencies import get_message_orchestrator_factory
from backend.app.api.routes.whatsapp import receive_whatsapp_webhook
from backend.app.core.config import HttpSettings, Settings, get_settings
from backend.app.core.exceptions import AIProviderRateLimitError
from backend.app.core.logging import HTTP_LOGGER_NAME, WHATSAPP_BACKGROUND_LOGGER_NAME
from backend.app.main import create_app
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.idempotency_store import InMemoryIdempotencyStore
from backend.app.services.message_orchestrator import MessageOrchestrator

WEBHOOK_PATH = "/api/v1/whatsapp/webhook"
WEBHOOK_TOKEN = "test-only-green-api-webhook-token"
INSTANCE_ID = "123456789012"


class RecordingMessageOrchestrator:
    def __init__(self) -> None:
        self.messages: list[InboundMessage] = []

    async def process_message(self, message: InboundMessage) -> bool:
        self.messages.append(message)
        return True


class RecordingBackgroundProcessor:
    def __init__(self) -> None:
        self.calls: list[tuple[tuple[InboundMessage, ...], Settings, str]] = []

    async def process_messages(
        self,
        messages: tuple[InboundMessage, ...],
        settings: Settings,
        request_id: str,
    ) -> None:
        self.calls.append((messages, settings, request_id))


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
        return "3EB0C767D097B7C7C030"


def make_application(
    webhook_token: str | None = WEBHOOK_TOKEN,
    instance_id: str | None = INSTANCE_ID,
    orchestrator: MessageOrchestrator | RecordingMessageOrchestrator | None = None,
) -> FastAPI:
    application = create_app(HttpSettings(app_env="testing", log_level="INFO", _env_file=None))
    settings = Settings(
        assistant_branch_code="sucursal-demo",
        openai_api_key="test-only-openai-credential-placeholder",
        green_api_webhook_token=webhook_token,
        green_api_instance_id=instance_id,
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


def text_message_payload(
    chat_id: str,
    text: str,
    *,
    message_id: str = "F7AEC1B7086ECDC7E6E45923F5EDB825",
    instance_id: int = 123_456_789_012,
) -> bytes:
    payload = {
        "typeWebhook": "incomingMessageReceived",
        "instanceData": {
            "idInstance": instance_id,
            "wid": "5215559999999@c.us",
            "typeInstance": "whatsapp",
        },
        "timestamp": 1_720_000_000,
        "idMessage": message_id,
        "senderData": {
            "chatId": chat_id,
            "sender": chat_id,
            "senderName": "Cliente",
        },
        "messageData": {
            "typeMessage": "textMessage",
            "textMessageData": {"textMessage": text},
        },
    }
    return json.dumps(payload, separators=(",", ":")).encode()


def authorization_headers(token: str = WEBHOOK_TOKEN) -> list[tuple[str, str]]:
    return [("Authorization", f"Bearer {token}")]


async def send_webhook(
    application: FastAPI,
    raw_body: bytes,
    headers: list[tuple[str, str]],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post(WEBHOOK_PATH, content=raw_body, headers=headers)


def make_direct_request(raw_body: bytes, webhook_token: str, request_id: str) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": WEBHOOK_PATH,
        "raw_path": WEBHOOK_PATH.encode("ascii"),
        "query_string": b"",
        "headers": [(b"authorization", f"Bearer {webhook_token}".encode("ascii"))],
        "scheme": "http",
        "server": ("testserver", 80),
        "client": ("127.0.0.1", 12345),
    }
    body_available = True

    async def receive() -> dict[str, object]:
        nonlocal body_available
        if body_available:
            body_available = False
            return {"type": "http.request", "body": raw_body, "more_body": False}
        return {"type": "http.disconnect"}

    request = Request(scope, receive)
    request.state.request_id = request_id
    return request


def test_get_handshake_is_not_exposed_for_green_api() -> None:
    application = make_application()

    async def send_get() -> httpx.Response:
        transport = httpx.ASGITransport(app=application)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            return await client.get(WEBHOOK_PATH)

    response = asyncio.run(send_get())

    assert response.status_code == 405


def test_valid_bearer_authorization_is_accepted() -> None:
    application = make_application()

    response = asyncio.run(send_webhook(application, b"{}", authorization_headers()))

    assert response.status_code == 200
    assert response.content == b""


def test_authenticated_text_message_completes_chat_and_outbound_flow_with_mocks() -> None:
    chat_id = "5215550000001@c.us"
    inbound_text = "test-only-private-inbound-text-marker"
    answer = "test-only-private-answer-marker"
    chat_service = FakeChatResponder(answer=answer)
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    application = make_application(orchestrator=orchestrator)
    raw_body = text_message_payload(chat_id, f"  {inbound_text}  ")

    response = asyncio.run(send_webhook(application, raw_body, authorization_headers()))

    assert response.status_code == 200
    assert response.content == b""
    assert chat_service.messages == [inbound_text]
    assert whatsapp_client.calls == [(chat_id, answer, False)]


def test_authenticated_route_queues_work_without_awaiting_external_processing() -> None:
    request_id = "background-scheduling-request-id"
    raw_body = text_message_payload("5215550000001@c.us", "mensaje diferido")
    request = make_direct_request(raw_body, WEBHOOK_TOKEN, request_id)
    background_tasks = BackgroundTasks()
    background_processor = RecordingBackgroundProcessor()
    settings = Settings(
        assistant_branch_code="sucursal-demo",
        openai_api_key="test-only-openai-credential-placeholder",
        green_api_webhook_token=WEBHOOK_TOKEN,
        green_api_instance_id=INSTANCE_ID,
        _env_file=None,
    )

    async def schedule_then_run() -> tuple[object, int, int]:
        response = await receive_whatsapp_webhook(
            request,
            background_tasks,
            settings,
            background_processor,  # type: ignore[arg-type]
        )
        calls_before_response = len(background_processor.calls)
        queued_tasks = len(background_tasks.tasks)
        await background_tasks()
        return response, calls_before_response, queued_tasks

    response, calls_before_response, queued_tasks = asyncio.run(schedule_then_run())

    assert response.status_code == 200
    assert response.body == b""
    assert calls_before_response == 0
    assert queued_tasks == 1
    assert len(background_processor.calls) == 1
    messages, received_settings, received_request_id = background_processor.calls[0]
    assert len(messages) == 1
    assert messages[0].text == "mensaje diferido"
    assert received_settings is settings
    assert received_request_id == request_id


def test_duplicate_authenticated_message_id_is_acked_without_a_second_response() -> None:
    chat_id = "5215550000001@c.us"
    inbound_text = "test-only-duplicate-inbound-text-marker"
    answer = "test-only-single-answer-marker"
    chat_service = FakeChatResponder(answer=answer)
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    application = make_application(orchestrator=orchestrator)
    raw_body = text_message_payload(chat_id, inbound_text)

    async def send_twice() -> tuple[httpx.Response, httpx.Response]:
        first = await send_webhook(application, raw_body, authorization_headers())
        second = await send_webhook(application, raw_body, authorization_headers())
        return first, second

    first_response, duplicate_response = asyncio.run(send_twice())

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 200
    assert first_response.content == duplicate_response.content == b""
    assert chat_service.messages == [inbound_text]
    assert whatsapp_client.calls == [(chat_id, answer, False)]


def test_background_chat_failure_keeps_ack_and_logs_safe_category_without_leaking_data(
    caplog: pytest.LogCaptureFixture,
) -> None:
    chat_id = "5215550000001@c.us"
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
    application = make_application(orchestrator=orchestrator)
    raw_body = text_message_payload(chat_id, inbound_text)

    with caplog.at_level(logging.INFO):
        response = asyncio.run(send_webhook(application, raw_body, authorization_headers()))

    assert response.status_code == 200
    assert response.content == b""
    assert whatsapp_client.calls == []
    rendered = f"{response.text}\n{caplog.text}"
    assert chat_id not in rendered
    assert inbound_text not in rendered
    assert answer not in rendered
    assert internal_detail not in rendered
    assert "background_message_processing_failed" in caplog.text
    assert "error_category=message_processing_failed" in caplog.text
    assert WHATSAPP_BACKGROUND_LOGGER_NAME in caplog.text


def test_unauthenticated_payload_is_rejected_before_body_is_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    body_was_read = False

    async def track_body_access(request: Request) -> bytes:
        nonlocal body_was_read
        body_was_read = True
        return b"{}"

    monkeypatch.setattr(Request, "body", track_body_access)
    application = make_application()

    response = asyncio.run(
        send_webhook(application, b'{"untrusted":"payload"}', authorization_headers("wrong"))
    )

    assert response.status_code == 403
    assert response.content == b""
    assert body_was_read is False


def test_unauthenticated_text_does_not_build_provider_adapters() -> None:
    application = make_application()
    application.dependency_overrides.pop(get_message_orchestrator_factory)
    raw_body = text_message_payload("5215550000001@c.us", "texto no autenticado")

    response = asyncio.run(send_webhook(application, raw_body, authorization_headers("wrong")))

    assert response.status_code == 403
    assert response.content == b""


@pytest.mark.parametrize(
    "headers",
    (
        [],
        [("Authorization", "Basic test-only-token")],
        [("Authorization", "Bearer")],
        [("Authorization", "Bearer wrong-token")],
        [("Authorization", "Bearer " + "x" * 2049)],
        [
            ("Authorization", f"Bearer {WEBHOOK_TOKEN}"),
            ("Authorization", f"Bearer {WEBHOOK_TOKEN}"),
        ],
    ),
)
def test_missing_or_malformed_authorization_is_rejected(
    headers: list[tuple[str, str]],
) -> None:
    application = make_application()

    response = asyncio.run(send_webhook(application, b"{}", headers))

    assert response.status_code == 403
    assert response.content == b""


def test_invalid_authorization_does_not_expose_or_log_secret_body_or_header(
    caplog: pytest.LogCaptureFixture,
) -> None:
    body_marker = "test-only-private-body-marker"
    invalid_authorization = "Bearer test-only-invalid-webhook-token"
    application = make_application()

    with caplog.at_level(logging.WARNING, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(
            send_webhook(
                application,
                body_marker.encode("utf-8"),
                [("Authorization", invalid_authorization)],
            )
        )

    assert response.status_code == 403
    assert response.content == b""
    assert WEBHOOK_TOKEN not in caplog.text
    assert body_marker not in caplog.text
    assert invalid_authorization not in caplog.text


@pytest.mark.parametrize(
    ("webhook_token", "instance_id"),
    ((None, INSTANCE_ID), (WEBHOOK_TOKEN, None)),
)
def test_missing_green_api_webhook_configuration_fails_closed(
    webhook_token: str | None,
    instance_id: str | None,
) -> None:
    application = make_application(webhook_token=webhook_token, instance_id=instance_id)

    response = asyncio.run(send_webhook(application, b"{}", authorization_headers()))

    assert response.status_code == 503
    assert response.content == b""


@pytest.mark.parametrize(
    "raw_body",
    (
        b"not-json",
        b"[]",
        b'{"typeWebhook":"incomingMessageReceived","instanceData":"unexpected"}',
    ),
)
def test_authenticated_unusual_payload_does_not_break_webhook(raw_body: bytes) -> None:
    application = make_application()

    response = asyncio.run(send_webhook(application, raw_body, authorization_headers()))

    assert response.status_code == 200
    assert response.content == b""


def test_wrong_instance_is_acked_without_scheduling_processing() -> None:
    orchestrator = RecordingMessageOrchestrator()
    application = make_application(orchestrator=orchestrator)
    raw_body = text_message_payload(
        "5215550000001@c.us",
        "mensaje de otra instancia",
        instance_id=123_456_789_013,
    )

    response = asyncio.run(send_webhook(application, raw_body, authorization_headers()))

    assert response.status_code == 200
    assert orchestrator.messages == []


def test_authenticated_payload_body_and_authorization_are_not_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    body_marker = "test-only-private-text-body-marker"
    raw_body = text_message_payload("5215550000001@c.us", body_marker)
    application = make_application()

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(send_webhook(application, raw_body, authorization_headers()))

    assert response.status_code == 200
    assert body_marker not in caplog.text
    assert raw_body.decode() not in caplog.text
    assert WEBHOOK_TOKEN not in caplog.text
