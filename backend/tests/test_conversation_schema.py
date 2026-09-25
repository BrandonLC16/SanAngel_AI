"""The WhatsApp schema keeps metadata minimal and enforces branch boundaries."""

from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, inspect, select
from sqlalchemy.exc import IntegrityError

from backend.app.core.config import get_database_settings
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.message import Message
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
USER_KEY = "a" * 64


@pytest.fixture
def engine(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Generator[Engine]:
    database_url = f"sqlite+pysqlite:///{(tmp_path / 'conversation-schema.db').as_posix()}"
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_database_settings.cache_clear()
    command.upgrade(Config(str(REPOSITORY_ROOT / "alembic.ini")), "head")
    database_engine = create_database_engine(database_url)
    try:
        yield database_engine
    finally:
        database_engine.dispose()
        get_database_settings.cache_clear()


def create_branches(engine: Engine) -> tuple[int, int]:
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        first = Branch(
            code="sucursal-uno",
            name="Sucursal uno",
            address="Dirección ficticia uno",
            business_hours="Lunes a viernes",
        )
        second = Branch(
            code="sucursal-dos",
            name="Sucursal dos",
            address="Dirección ficticia dos",
            business_hours="Sábado",
        )
        session.add_all((first, second))
        session.flush()
        return first.id, second.id


def test_migrated_tables_have_only_minimal_whatsapp_fields(engine: Engine) -> None:
    inspector = inspect(engine)
    assert {column["name"] for column in inspector.get_columns("conversations")} == {
        "id",
        "branch_id",
        "channel",
        "external_user_key",
        "created_at",
        "updated_at",
    }
    responder_columns = {
        column["name"] for column in inspector.get_columns("conversation_responder_states")
    }
    assert responder_columns == {
        "conversation_id",
        "branch_id",
        "mode",
        "assigned_admin_user_id",
        "ai_reply_count",
    }
    responder_checks = {
        item["name"] for item in inspector.get_check_constraints("conversation_responder_states")
    }
    assert responder_checks == {
        "ck_conversation_responder_mode",
        "ck_conversation_responder_ai_reply_count",
        "ck_conversation_responder_owner",
    }
    responder_foreign_keys = {
        item["name"] for item in inspector.get_foreign_keys("conversation_responder_states")
    }
    assert responder_foreign_keys == {
        "fk_conversation_responder_conversation_branch",
        "fk_conversation_responder_admin_branch",
    }
    assert {column["name"] for column in inspector.get_columns("messages")} == {
        "id",
        "branch_id",
        "conversation_id",
        "direction",
        "occurred_at",
    }
    assert {column["name"] for column in inspector.get_columns("whatsapp_event_receipts")} == {
        "id",
        "branch_id",
        "provider_message_id",
        "status",
        "received_at",
        "completed_at",
    }
    assert {item["name"] for item in inspector.get_unique_constraints("conversations")} == {
        "uq_conversations_branch_channel_user",
        "uq_conversations_id_branch_id",
    }
    assert {
        item["name"] for item in inspector.get_unique_constraints("whatsapp_event_receipts")
    } == {"uq_whatsapp_event_receipts_branch_message"}
    assert {item["name"] for item in inspector.get_check_constraints("conversations")} == {
        "ck_conversations_channel",
        "ck_conversations_external_user_key",
    }
    assert {item["name"] for item in inspector.get_check_constraints("messages")} == {
        "ck_messages_direction"
    }
    assert {
        item["name"] for item in inspector.get_check_constraints("whatsapp_event_receipts")
    } == {
        "ck_whatsapp_event_receipts_message_id",
        "ck_whatsapp_event_receipts_status",
    }
    assert {item["name"] for item in inspector.get_indexes("messages")} == {
        "ix_messages_branch_conversation_time"
    }
    assert {item["name"] for item in inspector.get_indexes("whatsapp_event_receipts")} == {
        "ix_whatsapp_event_receipts_branch_status_time"
    }
    assert {item["name"] for item in inspector.get_foreign_keys("conversations")} == {
        "fk_conversations_branch_id_branches"
    }
    assert {item["name"] for item in inspector.get_foreign_keys("messages")} == {
        "fk_messages_conversation_id_branch_id_conversations"
    }
    assert {item["name"] for item in inspector.get_foreign_keys("whatsapp_event_receipts")} == {
        "fk_whatsapp_event_receipts_branch_id_branches"
    }


def test_conversation_and_receipt_ids_are_unique_within_branch(engine: Engine) -> None:
    first_branch_id, second_branch_id = create_branches(engine)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        session.add_all(
            (
                Conversation(
                    branch_id=first_branch_id, channel="whatsapp", external_user_key=USER_KEY
                ),
                Conversation(
                    branch_id=second_branch_id, channel="whatsapp", external_user_key=USER_KEY
                ),
                WhatsAppEventReceipt(
                    branch_id=first_branch_id,
                    provider_message_id="provider-event-1",
                    status="claimed",
                ),
                WhatsAppEventReceipt(
                    branch_id=second_branch_id,
                    provider_message_id="provider-event-1",
                    status="claimed",
                ),
            )
        )

    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.add(
                Conversation(
                    branch_id=first_branch_id, channel="whatsapp", external_user_key=USER_KEY
                )
            )
            session.flush()

    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.add(
                WhatsAppEventReceipt(
                    branch_id=first_branch_id,
                    provider_message_id="provider-event-1",
                    status="claimed",
                )
            )
            session.flush()

    with factory() as session:
        assert len(session.scalars(select(Conversation)).all()) == 2
        assert len(session.scalars(select(WhatsAppEventReceipt)).all()) == 2


def test_message_cannot_reference_a_conversation_in_another_branch(engine: Engine) -> None:
    first_branch_id, second_branch_id = create_branches(engine)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        conversation = Conversation(
            branch_id=first_branch_id, channel="whatsapp", external_user_key=USER_KEY
        )
        session.add(conversation)
        session.flush()
        conversation_id = conversation.id
        session.add(
            Message(branch_id=first_branch_id, conversation_id=conversation_id, direction="inbound")
        )

    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.add(
                Message(
                    branch_id=second_branch_id,
                    conversation_id=conversation_id,
                    direction="outbound",
                )
            )
            session.flush()

    with factory() as session:
        messages = session.scalars(select(Message)).all()
        assert len(messages) == 1
        assert messages[0].branch_id == first_branch_id


def test_receipt_requires_an_existing_branch_and_valid_completion_time(engine: Engine) -> None:
    first_branch_id, _ = create_branches(engine)
    factory = create_database_session_factory(engine)
    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.add(
                WhatsAppEventReceipt(
                    branch_id=first_branch_id + 1000,
                    provider_message_id="provider-event-1",
                    status="claimed",
                )
            )
            session.flush()

    with factory.begin() as session:
        session.add(
            WhatsAppEventReceipt(
                branch_id=first_branch_id,
                provider_message_id="provider-event-1",
                status="claimed",
            )
        )
    with factory.begin() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        receipt.status = "completed"
        receipt.completed_at = receipt.received_at

    with factory() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        assert receipt.status == "completed"
        assert receipt.completed_at is not None


@pytest.mark.parametrize(
    ("model", "field_values"),
    (
        (Conversation, {"channel": "email", "external_user_key": USER_KEY}),
        (Conversation, {"channel": "whatsapp", "external_user_key": "raw-phone-number"}),
        (Conversation, {"channel": "whatsapp", "external_user_key": "A" * 64}),
        (Message, {"direction": "system"}),
        (WhatsAppEventReceipt, {"provider_message_id": " ", "status": "claimed"}),
        (WhatsAppEventReceipt, {"provider_message_id": "event-2", "status": "completed"}),
    ),
)
def test_database_rejects_invalid_channel_identity_direction_or_receipt_state(
    engine: Engine, model: type, field_values: dict[str, str]
) -> None:
    first_branch_id, _ = create_branches(engine)
    factory = create_database_session_factory(engine)
    with factory.begin() as session:
        conversation = Conversation(
            branch_id=first_branch_id, channel="whatsapp", external_user_key=USER_KEY
        )
        session.add(conversation)
        session.flush()
        conversation_id = conversation.id

    values: dict[str, object] = {"branch_id": first_branch_id, **field_values}
    if model is Message:
        values["conversation_id"] = conversation_id

    with pytest.raises(IntegrityError):
        with factory.begin() as session:
            session.add(model(**values))
            session.flush()
