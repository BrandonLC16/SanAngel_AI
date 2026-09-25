"""F7.4 retention, scoped erasure, and redacted operational output."""

import logging
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.cli.purge_whatsapp_metadata import main
from backend.app.core.config import AssistantSettings, ConversationIdentitySettings
from backend.app.core.exceptions import InvalidRequestError, ServiceUnavailableError
from backend.app.db.base import Base
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.manual_send_receipt import ManualSendReceipt
from backend.app.db.models.message import Message
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.conversation_identity_service import ConversationIdentityService
from backend.app.services.whatsapp_privacy_service import WhatsAppPrivacyService

NOW = datetime(2026, 9, 24, 12, tzinfo=UTC)
IDENTITY_KEY = "test-only-conversation-identity-key-0001"
SENDER_ID = "5215550000001@c.us"


@pytest.fixture
def sessions(tmp_path: Path) -> Generator[sessionmaker[Session]]:
    engine = create_database_engine(f"sqlite+pysqlite:///{(tmp_path / 'privacy.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        session.add_all(
            (
                Branch(
                    code="sucursal-uno",
                    name="Sucursal uno",
                    address="Dirección ficticia uno",
                    business_hours="Lunes a viernes",
                ),
                Branch(
                    code="sucursal-dos",
                    name="Sucursal dos",
                    address="Dirección ficticia dos",
                    business_hours="Sábado",
                ),
            )
        )
    try:
        yield factory
    finally:
        engine.dispose()


def settings(branch_code: str = "sucursal-uno") -> ConversationIdentitySettings:
    return ConversationIdentitySettings(
        assistant_branch_code=branch_code,
        conversation_identity_key=IDENTITY_KEY,
        _env_file=None,
    )


def branch_ids(sessions: sessionmaker[Session]) -> tuple[int, int]:
    with sessions() as session:
        first = session.scalar(select(Branch.id).where(Branch.code == "sucursal-uno"))
        second = session.scalar(select(Branch.id).where(Branch.code == "sucursal-dos"))
        assert first is not None and second is not None
        return first, second


def add_conversation(session: Session, branch_id: int, key: str, *, age_days: int) -> Conversation:
    conversation = Conversation(
        branch_id=branch_id,
        external_user_key=key,
        created_at=NOW - timedelta(days=age_days),
        updated_at=NOW - timedelta(days=age_days),
    )
    session.add(conversation)
    session.flush()
    session.add(ConversationResponderState(conversation_id=conversation.id, branch_id=branch_id))
    return conversation


def test_preview_and_purge_expired_metadata_only_in_configured_branch(
    sessions: sessionmaker[Session], caplog: pytest.LogCaptureFixture
) -> None:
    first_id, second_id = branch_ids(sessions)
    with sessions.begin() as session:
        old = add_conversation(session, first_id, "a" * 64, age_days=31)
        active = add_conversation(session, first_id, "b" * 64, age_days=1)
        cross_branch = add_conversation(session, second_id, "c" * 64, age_days=31)
        for conversation in (old, active, cross_branch):
            session.add(
                Message(
                    branch_id=conversation.branch_id,
                    conversation_id=conversation.id,
                    direction="inbound",
                    occurred_at=NOW - timedelta(days=31),
                )
            )
        session.add_all(
            (
                WhatsAppEventReceipt(
                    branch_id=first_id,
                    provider_message_id="completed-old",
                    status="completed",
                    received_at=NOW - timedelta(days=31),
                    completed_at=NOW - timedelta(days=31),
                ),
                WhatsAppEventReceipt(
                    branch_id=first_id,
                    provider_message_id="completed-recent",
                    status="completed",
                    completed_at=NOW - timedelta(days=1),
                ),
                WhatsAppEventReceipt(
                    branch_id=first_id,
                    provider_message_id="claimed-ambiguous",
                    status="claimed",
                    received_at=NOW - timedelta(days=31),
                ),
                WhatsAppEventReceipt(
                    branch_id=second_id,
                    provider_message_id="other-branch",
                    status="completed",
                    completed_at=NOW - timedelta(days=31),
                ),
            )
        )

    privacy = WhatsAppPrivacyService(sessions, settings=settings())
    with caplog.at_level(logging.INFO):
        preview = privacy.purge_expired(now=NOW)
        assert preview.conversations == 1
        assert preview.messages == 2
        assert preview.completed_receipts == 1
        assert preview.claimed_for_review == 1
        with sessions() as session:
            assert len(session.scalars(select(Conversation)).all()) == 3
            assert len(session.scalars(select(Message)).all()) == 3
        applied = privacy.purge_expired(now=NOW, apply=True)

    assert applied == preview
    with sessions() as session:
        conversations = session.scalars(select(Conversation)).all()
        states = session.scalars(select(ConversationResponderState)).all()
        messages = session.scalars(select(Message)).all()
        receipts = session.scalars(select(WhatsAppEventReceipt)).all()
    assert {item.external_user_key for item in conversations} == {"b" * 64, "c" * 64}
    assert {item.conversation_id for item in states} == {item.id for item in conversations}
    assert len(messages) == 1 and messages[0].branch_id == second_id
    assert {item.provider_message_id for item in receipts} == {
        "completed-recent",
        "claimed-ambiguous",
        "other-branch",
    }
    assert "completed-old" not in caplog.text
    assert "claimed-ambiguous" not in caplog.text
    assert "a" * 64 not in caplog.text


def test_recent_message_preserves_parent_when_conversation_timestamp_is_old(
    sessions: sessionmaker[Session],
) -> None:
    first_id, _ = branch_ids(sessions)
    with sessions.begin() as session:
        conversation = add_conversation(session, first_id, "d" * 64, age_days=31)
        session.add(
            Message(
                branch_id=first_id,
                conversation_id=conversation.id,
                direction="inbound",
                occurred_at=NOW - timedelta(days=1),
            )
        )
    result = WhatsAppPrivacyService(sessions, settings=settings()).purge_expired(
        apply=True, now=NOW
    )
    assert result.conversations == 0
    with sessions() as session:
        assert len(session.scalars(select(Conversation)).all()) == 1
        assert len(session.scalars(select(Message)).all()) == 1


def test_uncertain_manual_send_preserves_old_conversation_for_review(
    sessions: sessionmaker[Session],
) -> None:
    first_id, _ = branch_ids(sessions)
    with sessions.begin() as session:
        actor = AdminUser(
            branch_id=first_id,
            username="editor",
            password_hash="$argon2id$test-only-hash",
            role="editor",
        )
        session.add(actor)
        session.flush()
        conversation = add_conversation(session, first_id, "e" * 64, age_days=31)
        session.add(
            ManualSendReceipt(
                conversation_id=conversation.id,
                branch_id=first_id,
                actor_user_id=actor.id,
                request_id="00000000-0000-4000-8000-000000000001",
                status="uncertain",
            )
        )
    result = WhatsAppPrivacyService(sessions, settings=settings()).purge_expired(
        apply=True, now=NOW
    )
    assert result.conversations == 0
    with sessions() as session:
        assert session.scalars(select(Conversation)).all()
        assert session.scalars(select(ManualSendReceipt)).all()


def test_inactive_configured_branch_still_purges_expired_receipts(
    sessions: sessionmaker[Session],
) -> None:
    first_id, _ = branch_ids(sessions)
    with sessions.begin() as session:
        branch = session.get(Branch, first_id)
        assert branch is not None
        branch.is_active = False
        session.add(
            WhatsAppEventReceipt(
                branch_id=first_id,
                provider_message_id="completed-on-inactive-branch",
                status="completed",
                completed_at=NOW - timedelta(days=31),
            )
        )

    result = WhatsAppPrivacyService(sessions, settings=settings()).purge_expired(
        apply=True, now=NOW
    )
    assert result.completed_receipts == 1
    with sessions() as session:
        assert session.scalars(select(WhatsAppEventReceipt)).all() == []


def test_resolving_sender_refreshes_activity_for_retention(sessions: sessionmaker[Session]) -> None:
    first_id, _ = branch_ids(sessions)
    message = InboundMessage(
        external_message_id="test-only-message-id", sender_id=SENDER_ID, text="Hola"
    )
    with sessions.begin() as session:
        identity = ConversationIdentityService(session, settings=settings())
        context = identity.resolve(message)
        conversation = session.get(Conversation, context.conversation_id)
        assert conversation is not None
        conversation.updated_at = datetime.now(UTC) - timedelta(days=31)
    with sessions.begin() as session:
        ConversationIdentityService(session, settings=settings()).resolve(message)
    with sessions() as session:
        conversation = session.get(Conversation, context.conversation_id)
        assert conversation is not None
        assert conversation.branch_id == first_id
        assert conversation.updated_at.replace(tzinfo=UTC) > datetime.now(UTC) - timedelta(days=1)


def test_erase_sender_removes_only_scoped_conversation_and_omits_id_from_logs(
    sessions: sessionmaker[Session], caplog: pytest.LogCaptureFixture
) -> None:
    first_id, second_id = branch_ids(sessions)
    message = InboundMessage(
        external_message_id="test-only-message-id", sender_id=SENDER_ID, text="texto privado"
    )
    with sessions.begin() as session:
        own = ConversationIdentityService(session, settings=settings()).resolve(message)
        other_branch = ConversationIdentityService(
            session, settings=settings("sucursal-dos")
        ).resolve(message)
        session.add(
            Message(branch_id=first_id, conversation_id=own.conversation_id, direction="inbound")
        )
        session.add(
            Message(
                branch_id=second_id,
                conversation_id=other_branch.conversation_id,
                direction="inbound",
            )
        )
        session.add(
            WhatsAppEventReceipt(
                branch_id=first_id,
                provider_message_id="receipt-not-linked-to-sender",
                status="completed",
                completed_at=NOW,
            )
        )

    privacy = WhatsAppPrivacyService(sessions, settings=settings())
    with caplog.at_level(logging.INFO):
        assert privacy.erase_sender(SENDER_ID)
        assert not privacy.erase_sender(SENDER_ID)
    with sessions() as session:
        conversations = session.scalars(select(Conversation)).all()
        states = session.scalars(select(ConversationResponderState)).all()
        messages = session.scalars(select(Message)).all()
        receipts = session.scalars(select(WhatsAppEventReceipt)).all()
    assert len(conversations) == 1 and conversations[0].branch_id == second_id
    assert len(states) == 1 and states[0].conversation_id == other_branch.conversation_id
    assert len(messages) == 1 and messages[0].branch_id == second_id
    assert len(receipts) == 1
    assert SENDER_ID not in caplog.text
    assert "texto privado" not in caplog.text
    assert IDENTITY_KEY not in caplog.text


def test_invalid_sender_and_naive_time_fail_without_deleting(
    sessions: sessionmaker[Session],
) -> None:
    privacy = WhatsAppPrivacyService(sessions, settings=settings())
    with pytest.raises(InvalidRequestError) as exc_info:
        privacy.erase_sender("invalid@c.us")
    assert "invalid@c.us" not in str(exc_info.value)
    with pytest.raises(ValueError):
        privacy.purge_expired(now=datetime(2026, 9, 24))


def test_purge_needs_only_branch_scope_but_individual_erasure_requires_key(
    sessions: sessionmaker[Session],
) -> None:
    scoped_settings = AssistantSettings(assistant_branch_code="sucursal-uno", _env_file=None)
    privacy = WhatsAppPrivacyService(sessions, settings=scoped_settings)
    assert privacy.purge_expired(now=NOW).conversations == 0
    with pytest.raises(ServiceUnavailableError):
        privacy.erase_sender(SENDER_ID)


def test_cli_preview_then_apply_outputs_only_counts(
    sessions: sessionmaker[Session],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first_id, _ = branch_ids(sessions)
    old_date = datetime.now(UTC) - timedelta(days=31)
    with sessions.begin() as session:
        session.add(
            WhatsAppEventReceipt(
                branch_id=first_id,
                provider_message_id="private-provider-message-id",
                status="completed",
                received_at=old_date,
                completed_at=old_date,
            )
        )
    monkeypatch.setenv("ASSISTANT_BRANCH_CODE", "sucursal-uno")
    monkeypatch.delenv("CONVERSATION_IDENTITY_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{(tmp_path / 'privacy.db').as_posix()}")
    assert main([]) == 0
    preview_output = capsys.readouterr().out
    assert "recibos_completados=1" in preview_output
    with sessions() as session:
        assert len(session.scalars(select(WhatsAppEventReceipt)).all()) == 1

    assert main(["--apply"]) == 0
    applied_output = capsys.readouterr().out
    assert "recibos_completados=1" in applied_output
    with sessions() as session:
        assert session.scalars(select(WhatsAppEventReceipt)).all() == []
    assert "private-provider-message-id" not in preview_output + applied_output
    assert IDENTITY_KEY not in preview_output + applied_output
