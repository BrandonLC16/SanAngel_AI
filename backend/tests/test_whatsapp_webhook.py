import asyncio
import logging

import httpx
import pytest
from fastapi import FastAPI

from backend.app.core.config import HttpSettings, Settings, get_settings
from backend.app.core.logging import HTTP_LOGGER_NAME
from backend.app.main import create_app

WEBHOOK_PATH = "/api/v1/whatsapp/webhook"


def make_application(verify_token: str | None) -> FastAPI:
    application = create_app(HttpSettings(app_env="testing", log_level="INFO", _env_file=None))
    settings = Settings(
        openai_api_key="test-only-openai-credential-placeholder",
        whatsapp_verify_token=verify_token,
        _env_file=None,
    )
    application.dependency_overrides[get_settings] = lambda: settings
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
    application = make_application(None)

    response = asyncio.run(
        send_handshake(application, valid_params("test-only-verify-token-marker"))
    )

    assert response.status_code == 503
    assert response.content == b""
