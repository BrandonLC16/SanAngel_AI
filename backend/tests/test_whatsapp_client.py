import asyncio
import json
import logging
from collections.abc import Awaitable, Callable

import httpx
import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    WhatsAppClientConfigurationError,
    WhatsAppClientInputError,
    WhatsAppProviderConnectionError,
    WhatsAppProviderRateLimitError,
    WhatsAppProviderResponseError,
    WhatsAppProviderStatusError,
    WhatsAppProviderTimeoutError,
)
from backend.app.services.whatsapp_client import MAX_OUTBOUND_TEXT_CHARS, WhatsAppClient

ACCESS_TOKEN_MARKER = "test-only-whatsapp-access-token-marker"
PHONE_NUMBER_ID = "100000000000001"
RECIPIENT = "5215550000001"

Handler = Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]]


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "openai_api_key": "test-only-openai-credential-placeholder",
        "whatsapp_access_token": ACCESS_TOKEN_MARKER,
        "whatsapp_phone_number_id": PHONE_NUMBER_ID,
        "meta_graph_api_version": "v25.0",
        "whatsapp_request_timeout_seconds": 17.5,
        "_env_file": None,
    }
    values.update(overrides)
    return Settings(**values)


def run_with_mock_transport(
    handler: Handler,
    action: Callable[[WhatsAppClient], Awaitable[str]],
    *,
    settings: Settings | None = None,
) -> str:
    async def run() -> str:
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = WhatsAppClient(settings or make_settings(), http_client=http_client)
            return await action(client)

    return asyncio.run(run())


def test_send_text_uses_configured_url_header_timeout_and_official_payload() -> None:
    captured_request: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request.append(request)
        return httpx.Response(
            200,
            json={
                "messaging_product": "whatsapp",
                "contacts": [{"input": RECIPIENT, "wa_id": RECIPIENT}],
                "messages": [{"id": "wamid.test-only-outbound-message-id"}],
            },
        )

    message_id = run_with_mock_transport(
        handler,
        lambda client: client.send_text(RECIPIENT, "  Mensaje de prueba  ", preview_url=True),
    )

    assert message_id == "wamid.test-only-outbound-message-id"
    assert len(captured_request) == 1
    request = captured_request[0]
    assert str(request.url) == ("https://graph.facebook.com/v25.0/100000000000001/messages")
    assert request.url.query == b""
    assert request.headers["Authorization"] == f"Bearer {ACCESS_TOKEN_MARKER}"
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": RECIPIENT,
        "type": "text",
        "text": {"preview_url": True, "body": "Mensaje de prueba"},
    }
    assert set(request.extensions["timeout"].values()) == {17.5}
    assert ACCESS_TOKEN_MARKER not in str(request.url)
    assert ACCESS_TOKEN_MARKER.encode() not in request.content


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    (
        (302, WhatsAppProviderStatusError),
        (400, WhatsAppProviderStatusError),
        (429, WhatsAppProviderRateLimitError),
        (500, WhatsAppProviderStatusError),
    ),
)
def test_graph_api_status_errors_are_mapped(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": {"message": "provider detail"}})

    with pytest.raises(expected_error) as exc_info:
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))

    assert "provider detail" not in str(exc_info.value)
    assert ACCESS_TOKEN_MARKER not in str(exc_info.value)


@pytest.mark.parametrize(
    "response_content",
    (
        b"not-json",
        b"{}",
        b'{"messages":[]}',
        b'{"messages":[{}]}',
    ),
)
def test_invalid_success_response_is_mapped(response_content: bytes) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=response_content)

    with pytest.raises(WhatsAppProviderResponseError):
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))


@pytest.mark.parametrize(
    ("provider_error", "expected_error"),
    (
        (httpx.ReadTimeout("test timeout"), WhatsAppProviderTimeoutError),
        (httpx.ConnectError("test connection"), WhatsAppProviderConnectionError),
    ),
)
def test_transport_errors_are_mapped(
    provider_error: httpx.RequestError,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        provider_error.request = request
        raise provider_error

    with pytest.raises(expected_error) as exc_info:
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))

    assert "test timeout" not in str(exc_info.value)
    assert "test connection" not in str(exc_info.value)


@pytest.mark.parametrize(
    "recipient",
    (
        "",
        "12345",
        "0123456789",
        "+52 15550000001",
        "5215550000001?token=unsafe",
        "1" * 16,
    ),
)
def test_invalid_recipient_is_rejected_before_http(recipient: str) -> None:
    def reject_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid recipient reached HTTP transport")

    with pytest.raises(WhatsAppClientInputError):
        run_with_mock_transport(
            reject_request,
            lambda client: client.send_text(recipient, "Hola"),
        )


@pytest.mark.parametrize("text", ("", "   ", "x" * (MAX_OUTBOUND_TEXT_CHARS + 1)))
def test_invalid_text_is_rejected_before_http(text: str) -> None:
    def reject_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("invalid text reached HTTP transport")

    with pytest.raises(WhatsAppClientInputError):
        run_with_mock_transport(
            reject_request,
            lambda client: client.send_text(RECIPIENT, text),
        )


@pytest.mark.parametrize(
    "settings",
    (
        make_settings(whatsapp_access_token=None),
        make_settings(whatsapp_phone_number_id=None),
    ),
)
def test_missing_backend_configuration_fails_closed(settings: Settings) -> None:
    with pytest.raises(WhatsAppClientConfigurationError) as exc_info:
        WhatsAppClient(settings)

    assert ACCESS_TOKEN_MARKER not in str(exc_info.value)
    assert PHONE_NUMBER_ID not in str(exc_info.value)


def test_provider_failure_does_not_log_or_expose_token_recipient_or_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    recipient_marker = "+5215550000001"
    text_marker = "test-only-private-outbound-text-marker"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "private provider response"}})

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(WhatsAppProviderStatusError) as exc_info:
            run_with_mock_transport(
                handler,
                lambda client: client.send_text(recipient_marker, text_marker),
            )

    rendered = f"{exc_info.value}\n{caplog.text}"
    assert ACCESS_TOKEN_MARKER not in rendered
    assert recipient_marker not in rendered
    assert text_marker not in rendered
    assert "private provider response" not in rendered
