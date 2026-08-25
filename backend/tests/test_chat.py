import asyncio
import logging
import socket

import httpx
import pytest
from fastapi import FastAPI

from backend.app.api import dependencies
from backend.app.api.dependencies import get_chat_service
from backend.app.core.config import HttpSettings, Settings
from backend.app.core.exceptions import AIProviderRateLimitError
from backend.app.core.logging import HTTP_LOGGER_NAME
from backend.app.main import create_app
from backend.app.services.chat_service import ChatService

INVALID_PAYLOAD_MARKER = "private-invalid-payload-marker"


class FakeReplyGenerator:
    def __init__(
        self, *, answer: str = "respuesta simulada", error: Exception | None = None
    ) -> None:
        self.answer = answer
        self.error = error
        self.calls: list[str] = []

    async def generate_reply(self, message: str) -> str:
        self.calls.append(message)
        if self.error is not None:
            raise self.error
        return self.answer


def make_app(service: ChatService) -> FastAPI:
    application = create_app(HttpSettings(app_env="testing", log_level="INFO", _env_file=None))
    application.dependency_overrides[get_chat_service] = lambda: service
    return application


async def post_chat(application: FastAPI, message: str) -> httpx.Response:
    return await post_chat_payload(application, {"message": message})


async def post_chat_payload(
    application: FastAPI,
    payload: dict[str, object],
) -> httpx.Response:
    transport = httpx.ASGITransport(app=application)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        return await client.post("/api/v1/chat", json=payload)


def test_valid_message_returns_answer_without_network_or_content_logs(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    message_marker = "mensaje privado de prueba"
    answer_marker = "respuesta privada simulada"
    generator = FakeReplyGenerator(answer=answer_marker)
    application = make_app(ChatService(generator, max_message_chars=2000))

    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("chat endpoint test attempted a network connection")

    monkeypatch.setattr(socket, "getaddrinfo", reject_network)
    with caplog.at_level(logging.INFO, logger=HTTP_LOGGER_NAME):
        response = asyncio.run(post_chat(application, f"  {message_marker}  "))

    assert response.status_code == 200
    assert response.json() == {"answer": answer_marker}
    assert generator.calls == [message_marker]
    assert message_marker not in caplog.text
    assert answer_marker not in caplog.text


@pytest.mark.parametrize("message", ("", "   "))
def test_empty_or_blank_message_is_rejected_without_calling_provider(message: str) -> None:
    generator = FakeReplyGenerator()
    application = make_app(ChatService(generator, max_message_chars=2000))

    response = asyncio.run(post_chat(application, message))

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_request",
        "message": "La solicitud no es válida.",
    }
    assert generator.calls == []


def test_message_over_configured_limit_is_rejected_without_calling_provider() -> None:
    generator = FakeReplyGenerator()
    application = make_app(ChatService(generator, max_message_chars=5))

    response = asyncio.run(post_chat(application, "123456"))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert generator.calls == []


def test_default_dependency_connects_application_service_to_reply_provider(
    monkeypatch: pytest.MonkeyPatch,
    non_secret_credential: str,
) -> None:
    settings = Settings(
        openai_api_key=non_secret_credential,
        chat_max_message_chars=5,
        _env_file=None,
    )
    generator = FakeReplyGenerator(answer="respuesta conectada")
    received_settings: list[Settings] = []

    def fake_openai_service(candidate: Settings) -> FakeReplyGenerator:
        received_settings.append(candidate)
        return generator

    monkeypatch.setattr(dependencies, "get_settings", lambda: settings)
    monkeypatch.setattr(dependencies, "OpenAIService", fake_openai_service)
    get_chat_service.cache_clear()
    try:
        service = get_chat_service()
        answer = asyncio.run(service.answer("Hola"))
    finally:
        get_chat_service.cache_clear()

    assert answer == "respuesta conectada"
    assert received_settings == [settings]
    assert generator.calls == ["Hola"]


@pytest.mark.parametrize(
    "payload",
    (
        {},
        {"message": None},
        {"message": 123},
        {"message": INVALID_PAYLOAD_MARKER + ("x" * 10_001)},
    ),
)
def test_invalid_payload_is_rejected_without_echo_or_provider_call(
    payload: dict[str, object],
) -> None:
    generator = FakeReplyGenerator()
    application = make_app(ChatService(generator, max_message_chars=2000))

    response = asyncio.run(post_chat_payload(application, payload))

    assert response.status_code == 422
    assert response.json()["error"] == {
        "code": "invalid_request",
        "message": "La solicitud no es válida.",
    }
    assert INVALID_PAYLOAD_MARKER not in response.text
    assert generator.calls == []


def test_provider_failure_returns_controlled_error_without_internal_detail() -> None:
    internal_marker = "private-provider-failure"
    generator = FakeReplyGenerator(error=AIProviderRateLimitError(internal_marker))
    application = make_app(ChatService(generator, max_message_chars=2000))

    response = asyncio.run(post_chat(application, "Hola"))

    assert response.status_code == 503
    assert response.json()["error"] == {
        "code": "ai_service_unavailable",
        "message": "El asistente no está disponible temporalmente.",
    }
    assert internal_marker not in response.text
    assert "Traceback" not in response.text


def test_openapi_identifies_chat_as_internal_development_endpoint() -> None:
    application = make_app(ChatService(FakeReplyGenerator(), max_message_chars=2000))

    operation = application.openapi()["paths"]["/api/v1/chat"]["post"]

    assert operation["summary"] == "Chat interno de desarrollo"
    assert operation["tags"] == ["internal-development"]
    assert "no es el canal final" in operation["description"]
