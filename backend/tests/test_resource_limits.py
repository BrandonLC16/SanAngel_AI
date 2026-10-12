"""HTTP budgets reject abuse without consuming legitimate webhook capacity."""

import asyncio
import logging

import httpx
import pytest
from fastapi import Request

from backend.app.api.dependencies import get_chat_service
from backend.app.api.resource_limits import (
    MAX_ADMIN_JSON_BYTES,
    MAX_INTERNAL_CHAT_BYTES,
    MAX_WEBHOOK_BODY_BYTES,
    ResourceLimits,
    TokenBucket,
)
from backend.app.api.routes.admin_price_import import PriceImportReadTimeout, _bounded_workbook
from backend.app.core.config import HttpSettings
from backend.app.core.logging import HTTP_LOGGER_NAME
from backend.app.main import create_app
from backend.app.services.chat_service import ChatService
from backend.tests.test_whatsapp_webhook import (
    RecordingMessageOrchestrator,
    authorization_headers,
    make_application,
    send_webhook,
    text_message_payload,
)


def test_token_bucket_refills_after_burst_and_bounds_keys() -> None:
    now = [0.0]
    bucket = TokenBucket(
        rate_per_second=1,
        capacity=2,
        max_keys=2,
        clock=lambda: now[0],
    )
    assert bucket.allow("one")
    assert bucket.allow("one")
    assert not bucket.allow("one")
    now[0] = 0.5
    assert not bucket.allow("one")
    now[0] = 1.0
    assert bucket.allow("one")
    assert bucket.allow("two")
    assert bucket.allow("three")
    assert len(bucket._entries) == 2


def test_default_webhook_budget_admits_documented_provider_burst() -> None:
    limits = ResourceLimits(HttpSettings(app_env="testing", _env_file=None))
    assert all(limits.webhook.allow("configured-instance") for _ in range(50))


def test_admin_and_chat_limits_ignore_untrusted_forwarded_headers() -> None:
    app = create_app(
        HttpSettings(
            app_env="testing",
            admin_requests_per_minute=2,
            internal_requests_per_minute=1,
            _env_file=None,
        )
    )

    async def exercise() -> tuple[list[int], int, int, int]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            admin = [
                (
                    await client.get(
                        "/api/v1/admin/nonexistent",
                        headers={"X-Forwarded-For": f"untrusted-{index}"},
                    )
                ).status_code
                for index in range(3)
            ]
            health = (await client.get("/health")).status_code
            chat_first = (await client.post("/api/v1/chat", json={})).status_code
            chat_second = (await client.post("/api/v1/chat", json={})).status_code
            return admin, health, chat_first, chat_second

    admin, health, chat_first, chat_second = asyncio.run(exercise())
    assert admin == [404, 404, 429]
    assert health == 200
    assert chat_first == 422
    assert chat_second == 429


def test_admin_and_internal_body_limits_apply_to_declared_and_chunked_content() -> None:
    app = create_app(HttpSettings(app_env="testing", _env_file=None))

    async def chunks():
        yield b"x" * MAX_ADMIN_JSON_BYTES
        yield b"x"

    async def exercise() -> tuple[int, int, int]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            declared = await client.post(
                "/api/v1/admin/nonexistent", content=b"x" * (MAX_ADMIN_JSON_BYTES + 1)
            )
            chunked = await client.post("/api/v1/admin/nonexistent", content=chunks())
            internal = await client.post(
                "/api/v1/chat", content=b"x" * (MAX_INTERNAL_CHAT_BYTES + 1)
            )
            return declared.status_code, chunked.status_code, internal.status_code

    assert asyncio.run(exercise()) == (413, 413, 413)


def test_valid_chunked_internal_json_reaches_chat_service_after_bounded_read() -> None:
    app = create_app(HttpSettings(app_env="testing", _env_file=None))

    class FakeGenerator:
        async def generate_reply(self, message: str) -> str:
            assert message == "hola"
            return "respuesta de prueba"

    app.dependency_overrides[get_chat_service] = lambda: ChatService(
        FakeGenerator(), max_message_chars=2000
    )

    async def chunks():
        yield b'{"message":'
        yield b'"hola"}'

    async def exercise() -> tuple[int, dict[str, str]]:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/chat", content=chunks(), headers={"Content-Type": "application/json"}
            )
            return response.status_code, response.json()

    assert asyncio.run(exercise()) == (200, {"answer": "respuesta de prueba"})


def test_authenticated_webhook_burst_retries_and_invalid_tokens_do_not_spend_quota() -> None:
    orchestrator = RecordingMessageOrchestrator()
    app = make_application(orchestrator=orchestrator)
    app.state.resource_limits = ResourceLimits(
        HttpSettings(app_env="testing", webhook_requests_per_second=1, _env_file=None)
    )

    async def exercise() -> tuple[list[int], list[int], str | None]:
        invalid = [
            (await send_webhook(app, b"{}", authorization_headers("wrong-token"))).status_code
            for _ in range(3)
        ]
        valid_body = text_message_payload("5215550000001@c.us", "mensaje de prueba")
        valid = [await send_webhook(app, valid_body, authorization_headers()) for _ in range(3)]
        return (
            invalid,
            [response.status_code for response in valid],
            valid[-1].headers.get("Retry-After"),
        )

    invalid, valid, retry_after = asyncio.run(exercise())
    assert invalid == [403, 403, 403]
    assert valid == [200, 200, 429]
    assert retry_after == "1"
    assert len(orchestrator.messages) == 2


def test_oversized_authenticated_webhook_is_acked_without_processing_or_content_logs(
    caplog,
) -> None:
    orchestrator = RecordingMessageOrchestrator()
    app = make_application(orchestrator=orchestrator)
    body_marker = b"private-oversized-webhook-body"
    body = text_message_payload("5215550000001@c.us", body_marker.decode())
    body += b" " * (MAX_WEBHOOK_BODY_BYTES + 1)

    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(send_webhook(app, body, authorization_headers()))

    assert response.status_code == 200
    assert response.content == b""
    assert orchestrator.messages == []
    assert "error_category=webhook_body_rejected" in caplog.text
    assert body_marker.decode() not in caplog.text


def test_chunked_oversized_webhook_is_acked_without_processing() -> None:
    orchestrator = RecordingMessageOrchestrator()
    app = make_application(orchestrator=orchestrator)
    valid_prefix = text_message_payload("5215550000001@c.us", "mensaje de prueba")

    async def chunks():
        yield valid_prefix
        yield b" " * MAX_WEBHOOK_BODY_BYTES

    async def exercise() -> int:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/whatsapp/webhook", content=chunks(), headers=authorization_headers()
            )
            return response.status_code

    assert asyncio.run(exercise()) == 200
    assert orchestrator.messages == []


def test_slow_body_times_out_without_acknowledging_webhook() -> None:
    app = make_application()
    app.state.resource_limits = ResourceLimits(
        HttpSettings(app_env="testing", http_body_read_timeout_seconds=0.01, _env_file=None)
    )

    async def slow_body():
        await asyncio.sleep(0.05)
        yield b"{}"

    async def exercise() -> int:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post(
                "/api/v1/whatsapp/webhook",
                content=slow_body(),
                headers=authorization_headers(),
            )
            return response.status_code

    assert asyncio.run(exercise()) == 503


def test_slow_internal_body_gets_read_timeout() -> None:
    app = create_app(
        HttpSettings(app_env="testing", http_body_read_timeout_seconds=0.01, _env_file=None)
    )

    async def slow_body():
        await asyncio.sleep(0.05)
        yield b"{}"

    async def exercise() -> int:
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.post("/api/v1/chat", content=slow_body())
            return response.status_code

    assert asyncio.run(exercise()) == 408


def test_authenticated_price_import_stream_uses_same_read_deadline() -> None:
    app = create_app(
        HttpSettings(app_env="testing", http_body_read_timeout_seconds=0.01, _env_file=None)
    )
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/admin/price-import/preview",
        "headers": [
            (
                b"content-type",
                b"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        ],
        "app": app,
    }

    async def receive():
        await asyncio.sleep(0.05)
        return {"type": "http.request", "body": b"xlsx", "more_body": False}

    with pytest.raises(PriceImportReadTimeout) as exc_info:
        asyncio.run(_bounded_workbook(Request(scope, receive)))
    assert exc_info.value.status_code == 408
