import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.api import dependencies
from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import AssistantSettings, ConversationIdentitySettings, Settings
from backend.app.core.exceptions import (
    AIProviderRateLimitError,
    MessageProcessingError,
    WhatsAppProviderTimeoutError,
)
from backend.app.db.base import Base
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.conversation_mode_service import ConversationModeService
from backend.app.services.idempotency_store import InMemoryIdempotencyStore
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
        return "3EB0C767D097B7C7C030"


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
        external_message_id="F7AEC1B7086ECDC7E6E45923F5EDB825",
        sender_id="5215550000001@c.us",
        text=text,
        timestamp=1720000000,
    )


def test_process_message_connects_normalized_input_answer_and_sender() -> None:
    chat_service = FakeChatResponder(answer="Respuesta del chatbot")
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )

    result = asyncio.run(orchestrator.process_message(inbound_message(text="Pregunta")))

    assert result is True
    assert chat_service.messages == ["Pregunta"]
    assert whatsapp_client.calls == [("5215550000001@c.us", "Respuesta del chatbot", False)]


def test_default_factory_wires_cached_chat_and_closes_mocked_whatsapp_client(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    settings = Settings(
        assistant_branch_code="sucursal-demo",
        openai_api_key="test-only-openai-credential-placeholder",
        green_api_instance_id="1100000001",
        green_api_token_instance="test-only-green-api-token-placeholder",
        _env_file=None,
    )
    chat_service = FakeChatResponder(answer="Respuesta conectada")
    engine = create_database_engine(f"sqlite+pysqlite:///{(tmp_path / 'factory.db').as_posix()}")
    Base.metadata.create_all(engine)
    session_factory = create_database_session_factory(engine)
    with session_factory.begin() as session:
        session.add(
            Branch(
                code="sucursal-demo",
                name="Sucursal demo",
                address="Dirección ficticia",
                business_hours="Lunes a viernes",
            )
        )
    created_clients: list[ContextualFakeWhatsAppSender] = []

    def fake_whatsapp_client(candidate: Settings) -> ContextualFakeWhatsAppSender:
        client = ContextualFakeWhatsAppSender(candidate)
        created_clients.append(client)
        return client

    monkeypatch.setattr(dependencies, "get_chat_service", lambda: chat_service)
    monkeypatch.setattr(dependencies, "get_database_session_factory", lambda: session_factory)
    monkeypatch.setattr(
        dependencies,
        "get_conversation_identity_settings",
        lambda: ConversationIdentitySettings(
            assistant_branch_code="sucursal-demo",
            conversation_identity_key="test-only-conversation-identity-key-0001",
            _env_file=None,
        ),
    )
    monkeypatch.setattr(dependencies, "WhatsAppClient", fake_whatsapp_client)

    async def run_flow() -> None:
        async with dependencies.create_message_orchestrator(settings) as orchestrator:
            await orchestrator.process_message(inbound_message(text="Pregunta conectada"))

    try:
        asyncio.run(run_flow())
        with session_factory.begin() as session:
            conversation = session.scalar(select(Conversation))
            assert conversation is not None
            admin = AdminUser(
                branch_id=conversation.branch_id,
                username="editor",
                role="editor",
                password_hash="$argon2id$test",
            )
            session.add(admin)
            session.flush()
            principal = AdminSessionInfo(
                username=admin.username,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
                csrf_token="test-only-csrf",
                user_id=admin.id,
                branch_id=admin.branch_id,
                role=AdminRole.EDITOR,
            )
        modes = ConversationModeService(
            session_factory,
            settings=AssistantSettings(assistant_branch_code="sucursal-demo", _env_file=None),
        )
        modes.take(principal, conversation.id)

        async def run_human_mode() -> bool:
            async with dependencies.create_message_orchestrator(settings) as orchestrator:
                return await orchestrator.process_message(
                    InboundMessage(
                        external_message_id="test-only-second-message-id",
                        sender_id="5215550000001@c.us",
                        text="Pregunta para humano",
                    )
                )

        assert asyncio.run(run_human_mode()) is False
        with session_factory() as session:
            assert session.scalar(select(Conversation)) is not None
            receipts = session.scalars(select(WhatsAppEventReceipt)).all()
            assert len(receipts) == 2
            assert all(receipt.status == "completed" for receipt in receipts)
            state = session.scalar(select(ConversationResponderState))
            assert state is not None and state.mode == "HUMAN"
    finally:
        engine.dispose()

    assert len(created_clients) == 2
    whatsapp_client = created_clients[0]
    assert whatsapp_client.settings is settings
    assert whatsapp_client.entered is True
    assert whatsapp_client.closed is True
    assert chat_service.messages == ["Pregunta conectada"]
    assert whatsapp_client.calls == [("5215550000001@c.us", "Respuesta conectada", False)]
    assert created_clients[1].calls == []


def test_chat_failure_is_mapped_and_prevents_outbound_send() -> None:
    private_detail = "test-only-private-chat-failure-marker"
    chat_service = FakeChatResponder(error=AIProviderRateLimitError(private_detail))
    whatsapp_client = FakeWhatsAppSender()
    idempotency_store = InMemoryIdempotencyStore()
    orchestrator = MessageOrchestrator(chat_service, whatsapp_client, idempotency_store)

    with pytest.raises(MessageProcessingError) as exc_info:
        asyncio.run(orchestrator.process_message(inbound_message(text="texto privado")))

    assert whatsapp_client.calls == []
    assert private_detail not in str(exc_info.value)
    assert "texto privado" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.source_error_code == "ai_service_unavailable"
    assert exc_info.value.provider_code is None
    assert exc_info.value.provider_subcode is None
    assert asyncio.run(idempotency_store.claim("F7AEC1B7086ECDC7E6E45923F5EDB825"))


def test_outbound_failure_is_mapped_without_message_or_recipient_detail() -> None:
    private_detail = "test-only-private-whatsapp-failure-marker"
    chat_service = FakeChatResponder(answer="respuesta privada")
    whatsapp_client = FakeWhatsAppSender(error=WhatsAppProviderTimeoutError(private_detail))
    idempotency_store = InMemoryIdempotencyStore()
    orchestrator = MessageOrchestrator(chat_service, whatsapp_client, idempotency_store)

    with pytest.raises(MessageProcessingError) as exc_info:
        asyncio.run(orchestrator.process_message(inbound_message(text="texto privado")))

    assert private_detail not in str(exc_info.value)
    assert "5215550000001@c.us" not in str(exc_info.value)
    assert "texto privado" not in str(exc_info.value)
    assert "respuesta privada" not in str(exc_info.value)
    assert exc_info.value.__cause__ is None
    assert exc_info.value.source_error_code == "whatsapp_service_unavailable"
    assert exc_info.value.provider_code is None
    assert exc_info.value.provider_subcode is None
    assert not asyncio.run(idempotency_store.claim("F7AEC1B7086ECDC7E6E45923F5EDB825"))


def test_duplicate_message_id_does_not_generate_a_second_answer_or_send() -> None:
    chat_service = FakeChatResponder(answer="Respuesta única")
    whatsapp_client = FakeWhatsAppSender()
    orchestrator = MessageOrchestrator(
        chat_service,
        whatsapp_client,
        InMemoryIdempotencyStore(),
    )
    message = inbound_message(text="Pregunta repetida")

    async def process_twice() -> tuple[bool, bool]:
        first = await orchestrator.process_message(message)
        second = await orchestrator.process_message(message)
        return first, second

    results = asyncio.run(process_twice())

    assert results == (True, False)
    assert chat_service.messages == ["Pregunta repetida"]
    assert whatsapp_client.calls == [("5215550000001@c.us", "Respuesta única", False)]
