"""Offline WhatsApp-to-pending-panel handoff behavior."""

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import (
    AdminAuthSettings,
    ConversationIdentitySettings,
)
from backend.app.core.exceptions import AIProviderRateLimitError
from backend.app.db.base import Base
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.admin_review_service import AdminReviewService
from backend.app.services.branch_scope import BranchScope
from backend.app.services.conversation_identity_service import PersistentConversationContextResolver
from backend.app.services.conversation_mode_service import (
    ConversationModeService,
    PersistentConversationModeGate,
)
from backend.app.services.human_handoff_policy import HUMAN_HELP_ACK, explicitly_requests_human
from backend.app.services.message_orchestrator import MessageOrchestrator
from backend.app.services.persistent_idempotency_store import PersistentIdempotencyStore


class _Chat:
    def __init__(self, error: Exception | None) -> None:
        self.error = error
        self.calls = 0

    async def answer(self, _message: str) -> str:
        self.calls += 1
        if self.error:
            raise self.error
        return "Respuesta IA"


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ("¿Me puedes pasar con una asesora?", True),
        ("Necesito atención humana", True),
        ("humano", True),
        ("¿Cuánto cuesta la carne para una persona?", False),
        ("¿Hay empleados en la sucursal?", False),
    ],
)
def test_manual_request_rule_is_conservative(message: str, expected: bool) -> None:
    assert explicitly_requests_human(message) is expected


class _Sender:
    def __init__(self) -> None:
        self.texts: list[str] = []

    async def send_text(self, _recipient: str, text: str, *, preview_url: bool = False) -> str:
        self.texts.append(text)
        return "test-only-provider-id"


@pytest.mark.parametrize(
    ("text", "error", "reason", "expected_ai_calls"),
    [
        ("Quiero hablar con una persona", None, "customer_requested", 0),
        ("¿Qué tienen?", AIProviderRateLimitError(), "ai_unavailable", 1),
    ],
)
def test_request_reaches_only_own_panel_and_stops_ai(
    tmp_path: Path, text: str, error: Exception | None, reason: str, expected_ai_calls: int
) -> None:
    engine = create_database_engine(f"sqlite+pysqlite:///{(tmp_path / 'handoff.db').as_posix()}")
    Base.metadata.create_all(engine)
    sessions = create_database_session_factory(engine)
    identity = ConversationIdentitySettings(
        assistant_branch_code="sucursal-uno",
        conversation_identity_key="test-only-conversation-identity-key-0001",
        _env_file=None,
    )
    admin_settings = AdminAuthSettings(
        assistant_branch_code="sucursal-uno",
        admin_auth_key="test-only-admin-auth-key-0000000000001",
        _env_file=None,
    )
    with sessions.begin() as session:
        own = Branch(code="sucursal-uno", name="Uno", address="Prueba", business_hours="Lunes")
        foreign = Branch(code="sucursal-dos", name="Dos", address="Prueba", business_hours="Lunes")
        session.add_all([own, foreign])
        session.flush()
        viewer = AdminUser(
            branch_id=own.id, username="viewer", role="viewer", password_hash="$argon2id$test"
        )
        session.add(viewer)
        session.flush()
        principal = AdminSessionInfo(
            username=viewer.username,
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            csrf_token="test-only-csrf",
            user_id=viewer.id,
            branch_id=own.id,
            role=AdminRole.VIEWER,
        )
    chat = _Chat(error)
    sender = _Sender()
    flow = MessageOrchestrator(
        chat,
        sender,
        PersistentIdempotencyStore(sessions, branch_scope=BranchScope.from_settings(identity)),
        conversation_context_resolver=PersistentConversationContextResolver(
            sessions, settings=identity
        ),
        conversation_mode_gate=PersistentConversationModeGate(
            ConversationModeService(sessions, settings=identity)
        ),
    )
    first = InboundMessage(
        external_message_id="test-only-message-1", sender_id="5215550000001@c.us", text=text
    )
    followup = InboundMessage(
        external_message_id="test-only-message-2",
        sender_id=first.sender_id,
        text="Otra consulta",
    )
    try:
        assert asyncio.run(flow.process_message(first)) is True
        assert asyncio.run(flow.process_message(first)) is False
        assert asyncio.run(flow.process_message(followup)) is False
        assert chat.calls == expected_ai_calls
        assert sender.texts == [HUMAN_HELP_ACK]
        page = AdminReviewService(
            sessions, admin_settings=admin_settings, identity_settings=identity
        ).list_conversations(principal)
        assert len(page.items) == 1
        assert page.items[0].help_reason == reason
        assert page.items[0].help_requested_at is not None
        assert page.items[0].mode == "AI"
        with sessions() as session:
            state = session.scalar(select(ConversationResponderState))
            assert state is not None and state.ai_reply_count == 0
            assert [row.status for row in session.scalars(select(WhatsAppEventReceipt))] == [
                "completed",
                "completed",
            ]
    finally:
        engine.dispose()
