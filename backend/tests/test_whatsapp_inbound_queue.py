"""Durable, encrypted inbox and conservative worker recovery without provider traffic."""

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from backend.app.api.dependencies import get_inbound_queue_factory
from backend.app.cli import run_whatsapp_worker
from backend.app.core.config import (
    ConversationIdentitySettings,
    Settings,
    get_database_settings,
)
from backend.app.core.exceptions import BranchScopeMismatchError, ServiceUnavailableError
from backend.app.db.models.branch import Branch
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.models.whatsapp_inbound_job import WhatsAppInboundJob
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.branch_scope import BranchScope
from backend.app.services.message_orchestrator import MessageOrchestrator
from backend.app.services.persistent_idempotency_store import PersistentIdempotencyStore
from backend.app.services.whatsapp_inbound_queue import PersistentInboundQueue
from backend.app.services.whatsapp_inbound_worker import WhatsAppInboundWorker
from backend.tests.test_whatsapp_webhook import (
    authorization_headers,
    make_application,
    send_webhook,
    text_message_payload,
)

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def inbox(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    database_path = tmp_path / "inbox.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path.as_posix()}")
    get_database_settings.cache_clear()
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    engine = create_database_engine(f"sqlite+pysqlite:///{database_path.as_posix()}")
    sessions = create_database_session_factory(engine)
    with sessions.begin() as session:
        session.add(
            Branch(code="sucursal-demo", name="Demo", address="Calle 1", business_hours="Lunes")
        )
    identity = ConversationIdentitySettings(
        assistant_branch_code="sucursal-demo",
        conversation_identity_key="test-only-queue-identity-key-123456789",
        _env_file=None,
    )
    settings = Settings(
        assistant_branch_code="sucursal-demo",
        openai_api_key="test-only-openai-credential-placeholder",
        _env_file=None,
    )
    queue = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("sucursal-demo"), identity_settings=identity
    )
    try:
        yield queue, sessions, settings, identity
    finally:
        engine.dispose()
        get_database_settings.cache_clear()


def inbound(message_id: str = "event-1") -> InboundMessage:
    return InboundMessage(
        external_message_id=message_id,
        sender_id="5215550000001@c.us",
        text="private incoming question",
        timestamp=1_720_000_000,
    )


def test_pending_job_survives_restart_and_interrupted_claim_is_not_replayed(inbox) -> None:
    queue, sessions, _, identity = inbox
    message = inbound()
    assert asyncio.run(queue.enqueue((message,))) == 1
    assert asyncio.run(queue.enqueue((message,))) == 0
    with sessions() as session:
        row = session.scalar(select(WhatsAppInboundJob))
        assert row is not None
        assert message.sender_id not in row.payload_ciphertext
        assert message.text not in row.payload_ciphertext

    restarted = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("sucursal-demo"), identity_settings=identity
    )
    claimed = asyncio.run(restarted.claim_next())
    assert claimed is not None and claimed.message == message
    assert asyncio.run(queue.claim_next()) is None
    assert asyncio.run(queue.counts()) == {"pending": 0, "processing": 1, "uncertain": 0}
    asyncio.run(restarted.mark_uncertain(claimed.id))
    assert asyncio.run(queue.counts()) == {"pending": 0, "processing": 0, "uncertain": 1}
    assert asyncio.run(queue.claim_next()) is None


def test_worker_sends_once_then_receipt_deduplicates_later_webhook(inbox) -> None:
    queue, sessions, settings, _ = inbox
    sent: list[tuple[str, str]] = []

    class Chat:
        async def answer(self, text: str) -> str:
            return "Respuesta"

    class Sender:
        async def send_text(self, recipient: str, text: str, *, preview_url: bool = False) -> str:
            sent.append((recipient, text))
            return "outbound-1"

    @asynccontextmanager
    async def factory(_settings: Settings) -> AsyncIterator[MessageOrchestrator]:
        yield MessageOrchestrator(
            Chat(),
            Sender(),
            PersistentIdempotencyStore(sessions, branch_scope=BranchScope("sucursal-demo")),
        )

    message = inbound()
    assert asyncio.run(queue.enqueue((message,))) == 1
    worker = WhatsAppInboundWorker(queue, factory, settings)
    assert asyncio.run(worker.run_once()) is True
    assert sent == [(message.sender_id, "Respuesta")]
    assert asyncio.run(queue.counts()) == {"pending": 0, "processing": 0, "uncertain": 0}
    with sessions() as session:
        assert session.scalar(select(WhatsAppEventReceipt.status)) == "completed"
    assert asyncio.run(queue.enqueue((message,))) == 0
    assert asyncio.run(worker.run_once()) is False
    assert len(sent) == 1


def test_ambiguous_send_remains_uncertain_without_automatic_retry(inbox, caplog) -> None:
    queue, sessions, settings, _ = inbox
    attempts = 0

    class Chat:
        async def answer(self, text: str) -> str:
            return "Respuesta"

    class Sender:
        async def send_text(self, recipient: str, text: str, *, preview_url: bool = False) -> str:
            nonlocal attempts
            attempts += 1
            raise ServiceUnavailableError("private provider detail")

    @asynccontextmanager
    async def factory(_settings: Settings) -> AsyncIterator[MessageOrchestrator]:
        yield MessageOrchestrator(
            Chat(),
            Sender(),
            PersistentIdempotencyStore(sessions, branch_scope=BranchScope("sucursal-demo")),
        )

    message = inbound()
    asyncio.run(queue.enqueue((message,)))
    worker = WhatsAppInboundWorker(queue, factory, settings)
    assert asyncio.run(worker.run_once()) is True
    assert asyncio.run(worker.run_once()) is False
    assert attempts == 1
    assert asyncio.run(queue.counts())["uncertain"] == 1
    with sessions() as session:
        assert session.scalar(select(WhatsAppEventReceipt.status)) == "claimed"
    assert message.sender_id not in caplog.text
    assert message.text not in caplog.text
    assert "private provider detail" not in caplog.text


def test_queue_backpressure_rejects_new_message_without_ack(inbox, monkeypatch) -> None:
    queue, _, _, _ = inbox
    monkeypatch.setattr("backend.app.services.whatsapp_inbound_queue.MAX_PENDING_JOBS", 1)
    assert asyncio.run(queue.enqueue((inbound("event-1"),))) == 1
    with pytest.raises(ServiceUnavailableError):
        asyncio.run(queue.enqueue((inbound("event-2"),)))
    assert asyncio.run(queue.counts())["pending"] == 1


def test_concurrent_workers_claim_only_one_job(inbox) -> None:
    queue, sessions, _, identity = inbox
    peer = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("sucursal-demo"), identity_settings=identity
    )
    asyncio.run(queue.enqueue((inbound(),)))

    async def claim_both():
        return await asyncio.gather(queue.claim_next(), peer.claim_next())

    claims = asyncio.run(claim_both())
    assert sum(claim is not None for claim in claims) == 1


def test_queue_scope_rejects_other_branch_and_mismatched_identity_scope(inbox) -> None:
    queue, sessions, _, identity = inbox
    asyncio.run(queue.enqueue((inbound(),)))
    with sessions.begin() as session:
        session.add(
            Branch(code="otra-sucursal", name="Otra", address="Calle 2", business_hours="Lunes")
        )
    other_identity = ConversationIdentitySettings(
        assistant_branch_code="otra-sucursal",
        conversation_identity_key="test-only-queue-identity-key-123456789",
        _env_file=None,
    )
    other = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("otra-sucursal"), identity_settings=other_identity
    )
    assert asyncio.run(other.claim_next()) is None
    assert asyncio.run(other.counts())["pending"] == 0
    with pytest.raises(BranchScopeMismatchError):
        PersistentInboundQueue(
            sessions, branch_scope=BranchScope("otra-sucursal"), identity_settings=identity
        )


def test_wrong_encryption_key_quarantines_job_without_processing(inbox) -> None:
    queue, sessions, _, _ = inbox
    asyncio.run(queue.enqueue((inbound(),)))
    wrong_identity = ConversationIdentitySettings(
        assistant_branch_code="sucursal-demo",
        conversation_identity_key="test-only-other-identity-key-123456789",
        _env_file=None,
    )
    wrong_key_queue = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("sucursal-demo"), identity_settings=wrong_identity
    )
    with pytest.raises(ServiceUnavailableError):
        asyncio.run(wrong_key_queue.claim_next())
    assert asyncio.run(queue.counts())["uncertain"] == 1


def test_http_ack_follows_durable_commit_and_fifty_message_burst_is_admitted(inbox) -> None:
    queue, sessions, _, identity = inbox
    application = make_application()
    application.dependency_overrides[get_inbound_queue_factory] = lambda: lambda _settings: queue

    async def burst() -> list[int]:
        return [
            (
                await send_webhook(
                    application,
                    text_message_payload(
                        "5215550000001@c.us", "private question", message_id=f"burst-{i:04d}"
                    ),
                    authorization_headers(),
                )
            ).status_code
            for i in range(50)
        ]

    assert asyncio.run(burst()) == [200] * 50
    assert asyncio.run(queue.counts())["pending"] == 50
    restarted = PersistentInboundQueue(
        sessions, branch_scope=BranchScope("sucursal-demo"), identity_settings=identity
    )
    claimed = asyncio.run(restarted.claim_next())
    assert claimed is not None and claimed.message.external_message_id == "burst-0000"


def test_status_cli_reports_counts_without_payload(inbox, monkeypatch, capsys) -> None:
    queue, sessions, settings, identity = inbox
    asyncio.run(queue.enqueue((inbound(),)))
    monkeypatch.setattr(run_whatsapp_worker, "get_settings", lambda: settings)
    monkeypatch.setattr(run_whatsapp_worker, "get_conversation_identity_settings", lambda: identity)
    monkeypatch.setattr(run_whatsapp_worker, "get_database_session_factory", lambda: sessions)

    assert run_whatsapp_worker.main(["--status"]) == 0
    output = capsys.readouterr().out
    assert output.strip() == "pending=1 processing=0 uncertain=0"
    assert "private incoming question" not in output
    assert "5215550000001" not in output


def test_http_returns_503_when_persistent_queue_is_full(inbox, monkeypatch) -> None:
    queue, _, _, _ = inbox
    monkeypatch.setattr("backend.app.services.whatsapp_inbound_queue.MAX_PENDING_JOBS", 1)
    application = make_application()
    application.dependency_overrides[get_inbound_queue_factory] = lambda: lambda _settings: queue

    async def send_two() -> tuple[int, int, int]:
        first = await send_webhook(
            application,
            text_message_payload("5215550000001@c.us", "first", message_id="first"),
            authorization_headers(),
        )
        second = await send_webhook(
            application,
            text_message_payload("5215550000001@c.us", "second", message_id="second"),
            authorization_headers(),
        )
        duplicate = await send_webhook(
            application,
            text_message_payload("5215550000001@c.us", "first", message_id="first"),
            authorization_headers(),
        )
        return first.status_code, second.status_code, duplicate.status_code

    assert asyncio.run(send_two()) == (200, 503, 200)
    assert asyncio.run(queue.counts())["pending"] == 1
