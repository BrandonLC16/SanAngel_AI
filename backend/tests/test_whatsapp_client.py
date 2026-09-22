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

TOKEN_INSTANCE_MARKER = "test-only-green-api-token-instance-marker"
INSTANCE_ID = "1100000001"
RECIPIENT = "5215550000001@c.us"

Handler = Callable[[httpx.Request], httpx.Response | Awaitable[httpx.Response]]


def make_settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "assistant_branch_code": "sucursal-demo",
        "openai_api_key": "test-only-openai-credential-placeholder",
        "green_api_instance_id": INSTANCE_ID,
        "green_api_token_instance": TOKEN_INSTANCE_MARKER,
        "green_api_api_url": "https://1100.api.green-api.com",
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


def test_send_text_uses_configured_url_timeout_and_green_api_payload() -> None:
    captured_request: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_request.append(request)
        return httpx.Response(200, json={"idMessage": "3EB0C767D097B7C7C030"})

    message_id = run_with_mock_transport(
        handler,
        lambda client: client.send_text(RECIPIENT, "  Mensaje de prueba  ", preview_url=True),
    )

    assert message_id == "3EB0C767D097B7C7C030"
    assert len(captured_request) == 1
    request = captured_request[0]
    assert str(request.url) == (
        f"https://1100.api.green-api.com/waInstance1100000001/sendMessage/{TOKEN_INSTANCE_MARKER}"
    )
    assert request.url.query == b""
    assert "Authorization" not in request.headers
    assert request.headers["Content-Type"] == "application/json"
    assert json.loads(request.content) == {
        "chatId": RECIPIENT,
        "message": "Mensaje de prueba",
        "linkPreview": True,
    }
    assert set(request.extensions["timeout"].values()) == {17.5}
    assert TOKEN_INSTANCE_MARKER.encode() not in request.content


@pytest.mark.parametrize(
    ("status_code", "expected_error"),
    (
        (302, WhatsAppProviderStatusError),
        (400, WhatsAppProviderStatusError),
        (429, WhatsAppProviderRateLimitError),
        (500, WhatsAppProviderStatusError),
    ),
)
def test_green_api_status_errors_are_mapped(
    status_code: int,
    expected_error: type[Exception],
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"code": status_code, "description": "private"})

    with pytest.raises(expected_error) as exc_info:
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))

    assert "private" not in str(exc_info.value)
    assert TOKEN_INSTANCE_MARKER not in str(exc_info.value)


def test_green_api_status_error_retains_only_numeric_diagnostics() -> None:
    private_provider_detail = "test-only-private-provider-detail"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"code": 403, "description": private_provider_detail},
        )

    with pytest.raises(WhatsAppProviderStatusError) as exc_info:
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))

    assert exc_info.value.provider_code == 403
    assert exc_info.value.provider_subcode is None
    assert private_provider_detail not in str(exc_info.value)
    assert TOKEN_INSTANCE_MARKER not in str(exc_info.value)


def test_green_api_error_body_with_http_200_is_rejected() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"code": 401, "description": "private"})

    with pytest.raises(WhatsAppProviderStatusError) as exc_info:
        run_with_mock_transport(handler, lambda client: client.send_text(RECIPIENT, "Hola"))

    assert exc_info.value.provider_code == 401
    assert "private" not in str(exc_info.value)


@pytest.mark.parametrize(
    "response_content",
    (
        b"not-json",
        b"{}",
        b'{"idMessage":""}',
        b'{"idMessage":123}',
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
        "0123456789@c.us",
        "+5215550000001@c.us",
        "5215550000001",
        "5215550000001@c.us?token=unsafe",
        "not-a-chat@g.us",
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
        make_settings(green_api_instance_id=None),
        make_settings(green_api_token_instance=None),
    ),
)
def test_missing_backend_configuration_fails_closed(settings: Settings) -> None:
    with pytest.raises(WhatsAppClientConfigurationError) as exc_info:
        WhatsAppClient(settings)

    assert TOKEN_INSTANCE_MARKER not in str(exc_info.value)
    assert INSTANCE_ID not in str(exc_info.value)


def test_provider_failure_does_not_log_or_expose_token_recipient_or_text(
    caplog: pytest.LogCaptureFixture,
) -> None:
    text_marker = "test-only-private-outbound-text-marker"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"code": 500, "description": "private response"})

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(WhatsAppProviderStatusError) as exc_info:
            run_with_mock_transport(
                handler,
                lambda client: client.send_text(RECIPIENT, text_marker),
            )

    rendered = f"{exc_info.value}\n{caplog.text}"
    assert TOKEN_INSTANCE_MARKER not in rendered
    assert RECIPIENT not in rendered
    assert text_marker not in rendered
    assert "private response" not in rendered
