import asyncio
import logging
import socket
from dataclasses import dataclass
from secrets import token_urlsafe

import httpx2
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError, RateLimitError

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AIProviderConnectionError,
    AIProviderRateLimitError,
    AIProviderResponseError,
    AIProviderStatusError,
    AIProviderTimeoutError,
)
from backend.app.services import openai_service
from backend.app.services.openai_service import OpenAIService, load_base_system_prompt


@dataclass
class FakeResponse:
    output_text: str


class FakeResponsesAPI:
    def __init__(
        self,
        *,
        response: object | None = None,
        error: Exception | None = None,
    ) -> None:
        self.response = response or FakeResponse("respuesta simulada")
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def create(self, **kwargs: object) -> object:
        self.calls.append(kwargs)
        if self.error is not None:
            raise self.error
        return self.response


class FakeOpenAIClient:
    def __init__(self, responses: FakeResponsesAPI | None = None) -> None:
        self.responses = responses or FakeResponsesAPI()


def make_settings(**overrides: object) -> Settings:
    return Settings(
        openai_api_key=token_urlsafe(24),
        openai_model="configured-model",
        _env_file=None,
        **overrides,
    )


def test_base_system_prompt_contains_business_safety_rules() -> None:
    prompt = load_base_system_prompt()

    assert "Nunca inventes datos específicos del negocio" in prompt
    assert "precios, inventario, horarios, promociones ni sucursales" in prompt
    assert "credenciales" in prompt


@pytest.mark.parametrize("store_responses", (False, True))
def test_generate_reply_uses_responses_api_with_configurable_store_without_network(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    store_responses: bool,
) -> None:
    input_marker = "mensaje privado del cliente"
    output_marker = "respuesta privada del asistente"
    system_prompt = "instrucciones privadas"
    responses_api = FakeResponsesAPI(response=FakeResponse(f"  {output_marker}  "))
    client = FakeOpenAIClient(responses_api)
    service = OpenAIService(
        make_settings(openai_store_responses=store_responses),
        client=client,
        system_prompt=system_prompt,
    )

    def reject_network(*args: object, **kwargs: object) -> None:
        raise AssertionError("OpenAI service test attempted a network connection")

    monkeypatch.setattr(socket, "getaddrinfo", reject_network)
    with caplog.at_level(logging.DEBUG):
        result = asyncio.run(service.generate_reply(input_marker))

    assert result == output_marker
    assert responses_api.calls == [
        {
            "model": "configured-model",
            "instructions": system_prompt,
            "input": input_marker,
            "store": store_responses,
        }
    ]
    assert input_marker not in caplog.text
    assert output_marker not in caplog.text
    assert system_prompt not in caplog.text


def test_real_client_factory_receives_secret_timeout_and_bounded_retries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    secret_marker = token_urlsafe(24)
    captured_options: dict[str, object] = {}
    fake_client = FakeOpenAIClient()

    def fake_async_openai(**kwargs: object) -> FakeOpenAIClient:
        captured_options.update(kwargs)
        return fake_client

    monkeypatch.setattr(openai_service, "AsyncOpenAI", fake_async_openai)
    settings = Settings(
        openai_api_key=secret_marker,
        openai_timeout_seconds=17.5,
        openai_max_retries=1,
        _env_file=None,
    )

    service = OpenAIService(settings, system_prompt="prompt de prueba")

    assert service._client is fake_client
    assert captured_options == {
        "api_key": secret_marker,
        "timeout": 17.5,
        "max_retries": 1,
    }
    assert secret_marker not in repr(service)


def make_sdk_request() -> httpx2.Request:
    return httpx2.Request("POST", "https://api.openai.com/v1/responses")


def make_sdk_response(status_code: int) -> httpx2.Response:
    return httpx2.Response(status_code, request=make_sdk_request())


@pytest.mark.parametrize(
    ("sdk_error", "expected_error"),
    (
        (APITimeoutError(make_sdk_request()), AIProviderTimeoutError),
        (
            RateLimitError("rate limited", response=make_sdk_response(429), body=None),
            AIProviderRateLimitError,
        ),
        (
            APIConnectionError(request=make_sdk_request()),
            AIProviderConnectionError,
        ),
        (
            APIStatusError("provider error", response=make_sdk_response(500), body=None),
            AIProviderStatusError,
        ),
    ),
)
def test_provider_errors_are_mapped_to_internal_exceptions(
    sdk_error: Exception,
    expected_error: type[Exception],
) -> None:
    client = FakeOpenAIClient(FakeResponsesAPI(error=sdk_error))
    service = OpenAIService(
        make_settings(),
        client=client,
        system_prompt="prompt de prueba",
    )

    with pytest.raises(expected_error) as exc_info:
        asyncio.run(service.generate_reply("mensaje de prueba"))

    assert "api.openai.com" not in str(exc_info.value)


@pytest.mark.parametrize("output_text", ("", "   "))
def test_empty_provider_output_is_rejected(output_text: str) -> None:
    client = FakeOpenAIClient(FakeResponsesAPI(response=FakeResponse(output_text)))
    service = OpenAIService(
        make_settings(),
        client=client,
        system_prompt="prompt de prueba",
    )

    with pytest.raises(AIProviderResponseError):
        asyncio.run(service.generate_reply("mensaje de prueba"))


def test_provider_response_without_output_text_is_rejected() -> None:
    responses_api = FakeResponsesAPI(response=object())
    service = OpenAIService(
        make_settings(),
        client=FakeOpenAIClient(responses_api),
        system_prompt="prompt de prueba",
    )

    with pytest.raises(AIProviderResponseError):
        asyncio.run(service.generate_reply("mensaje de prueba"))
