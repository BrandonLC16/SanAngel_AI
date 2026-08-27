import asyncio

import pytest

from backend.app.api import dependencies
from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AIProviderRateLimitError,
    MessageProcessingError,
    WhatsAppProviderTimeoutError,
)
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.message_orchestrator import MessageOrchestrator


class FakeChatResponder:
    def __init__(self, *, answer: str = "respuesta simulada", error: Exception | None = None):
        self._answer = answer
        self.error = error
        self.messages: list[str] = []

    async def answer(self, message: str) -> str:
        self.messages.append(message)
        if self.error is not None:
            raise self.error
        return self._answer


class FakeWhatsAppSender:
    def __init__(self, *, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[tuple[str, str, bool]] = []

    async def send_text(
        self,
        recipient: str,
        text: str,
        *,
        preview_url: bool = False,
    ) -> str:
        self.calls.append((recipient, text, preview_url))
        if self.error is not None:
            raise self.error
        return "wamid.test-only-outbound-message-id"


class ContextualFakeWhatsAppSender(FakeWhatsAppSender):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.entered = False
        self.closed = False

    async def __aenter__(self) -> "ContextualFakeWhatsAppSender":
        self.entered = True
        return self

    async def __aexit__(self, *args: object) -> None:
        self.closed = True


def inbound_message(*, text: str = "Hola") -> InboundMessage:
    return InboundMessage(
        external_message_id="wamid.test-only-inbound-message-id",
        sender_id="5215550000001",
        text=text,
        timestamp=1720000000,
    )


def test_process_message_connects_normalized_input_answer_and_sender() -> None:
    chat_service = FakeChatResponder(answer="Respuesta del chatbot")
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(chat_service, whatsapp_client)

    result = asyncio.run(orchestrator.process_message(inbound_message(text="Pregunta")))

    assert result is None
    assert chat_service.messages == ["Pregunta"]
    assert whatsapp_client.calls == [("5215550000001", "Respuesta del chatbot", False)]


def test_default_factory_wires_cached_chat_and_closes_mocked_whatsapp_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(
        openai_api_key="test-only-openai-credential-placeholder",
        whatsapp_access_token="test-only-whatsapp-access-token-placeholder",
        whatsapp_phone_number_id="100000000000001",
        _env_file=None,
    )
    chat_service = FakeChatResponder(answer="Respuesta conectada")
    created_clients: list[ContextualFakeWhatsAppSender] = []

    def fake_whatsapp_client(candidate: Settings) -> ContextualFakeWhatsAppSender:
        client = ContextualFakeWhatsAppSender(candidate)
        created_clients.append(client)
        return client

    monkeypatch.setattr(dependencies, "get_chat_service", lambda: chat_service)
    monkeypatch.setattr(dependencies, "WhatsAppClient", fake_whatsapp_client)

    async def run_flow() -> None:
        async with dependencies.create_message_orchestrator(settings) as orchestrator:
            await orchestrator.process_message(inbound_message(text="Pregunta conectada"))

    asyncio.run(run_flow())

    assert len(created_clients) == 1
    whatsapp_client = created_clients[0]
    assert whatsapp_client.settings is settings
    assert whatsapp_client.entered is True
    assert whatsapp_client.closed is True
    assert chat_service.messages == ["Pregunta conectada"]
    assert whatsapp_client.calls == [("5215550000001", "Respuesta conectada", False)]


def test_chat_failure_is_mapped_and_prevents_outbound_send() -> None:
    private_detail = "test-only-private-chat-failure-marker"
    chat_service = FakeChatResponder(error=AIProviderRateLimitError(private_detail))
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(chat_service, whatsapp_client)

    with pytest.raises(MessageProcessingError) as exc_info:
        asyncio.run(orchestrator.process_message(inbound_message(text="texto privado")))

    assert whatsapp_client.calls == []
    assert private_detail not in str(exc_info.value)
    assert "texto privado" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None


def test_outbound_failure_is_mapped_without_message_or_recipient_detail() -> None:
    private_detail = "test-only-private-whatsapp-failure-marker"
    chat_service = FakeChatResponder(answer="respuesta privada")
    whatsapp_client = FakeWhatsAppSender(error=WhatsAppProviderTimeoutError(private_detail))
    orchestrator = MessageOrchestrator(chat_service, whatsapp_client)

    with pytest.raises(MessageProcessingError) as exc_info:
        asyncio.run(orchestrator.process_message(inbound_message(text="texto privado")))

    assert private_detail not in str(exc_info.value)
    assert "5215550000001" not in str(exc_info.value)
    assert "texto privado" not in str(exc_info.value)
    assert "respuesta privada" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
