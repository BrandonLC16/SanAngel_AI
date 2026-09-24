"""F7.3 receipt transactions, restarts, branch isolation, and duplicate races."""

import asyncio
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.exceptions import (
    AIProviderRateLimitError,
    BranchNotConfiguredError,
    IdempotencyStoreError,
    MessageProcessingError,
    WhatsAppProviderTimeoutError,
)
from backend.app.db.base import Base
from backend.app.db.models.branch import Branch
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.branch_scope import BranchScope
from backend.app.services.message_orchestrator import MessageOrchestrator
from backend.app.services.persistent_idempotency_store import PersistentIdempotencyStore

MESSAGE_ID = "test-only-inbound-message-id"


@pytest.fixture
def sessions(tmp_path: Path) -> Generator[sessionmaker[Session]]:
    engine = create_database_engine(f"sqlite+pysqlite:///{(tmp_path / 'receipts.db').as_posix()}")
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


def store(
    sessions: sessionmaker[Session], branch_code: str = "sucursal-uno"
) -> PersistentIdempotencyStore:
    return PersistentIdempotencyStore(sessions, branch_scope=BranchScope(branch_code))


def test_completed_receipt_survives_new_store_and_rejects_duplicate(
    sessions: sessionmaker[Session],
) -> None:
    first = store(sessions)

    async def run() -> None:
        assert await first.claim(MESSAGE_ID)
        await first.mark_processed(MESSAGE_ID)
        assert not await store(sessions).claim(MESSAGE_ID)

    asyncio.run(run())
    with sessions() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        assert receipt is not None
        assert receipt.provider_message_id == MESSAGE_ID
        assert receipt.status == "completed"
        assert receipt.completed_at is not None


def test_completed_receipt_survives_new_database_connection(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    async def run() -> None:
        identity_store = store(sessions)
        assert await identity_store.claim(MESSAGE_ID)
        await identity_store.mark_processed(MESSAGE_ID)

        second_engine = create_database_engine(
            f"sqlite+pysqlite:///{(tmp_path / 'receipts.db').as_posix()}"
        )
        try:
            second_factory = create_database_session_factory(second_engine)
            assert not await store(second_factory).claim(MESSAGE_ID)
        finally:
            second_engine.dispose()

    asyncio.run(run())


def test_concurrent_claims_across_store_instances_have_one_winner(
    sessions: sessionmaker[Session],
) -> None:
    stores = [store(sessions) for _ in range(12)]

    async def race() -> list[bool]:
        return list(await asyncio.gather(*(item.claim(MESSAGE_ID) for item in stores)))

    results = asyncio.run(race())
    assert results.count(True) == 1
    assert results.count(False) == 11
    with sessions() as session:
        assert len(session.scalars(select(WhatsAppEventReceipt)).all()) == 1


def test_receipts_are_scoped_to_configured_branch(sessions: sessionmaker[Session]) -> None:
    first = store(sessions, "sucursal-uno")
    second = store(sessions, "sucursal-dos")

    async def run() -> None:
        assert await first.claim(MESSAGE_ID)
        assert await second.claim(MESSAGE_ID)
        await first.mark_processed(MESSAGE_ID)
        await second.release(MESSAGE_ID)
        assert not await first.claim(MESSAGE_ID)
        assert await second.claim(MESSAGE_ID)

    asyncio.run(run())
    with sessions() as session:
        receipts = session.scalars(select(WhatsAppEventReceipt)).all()
    assert len(receipts) == 2
    assert {item.status for item in receipts} == {"claimed", "completed"}
    assert receipts[0].branch_id != receipts[1].branch_id


def test_inactive_configured_branch_cannot_claim_a_receipt(
    sessions: sessionmaker[Session],
) -> None:
    with sessions.begin() as session:
        branch = session.scalar(select(Branch).where(Branch.code == "sucursal-uno"))
        assert branch is not None
        branch.is_active = False

    with pytest.raises(BranchNotConfiguredError):
        asyncio.run(store(sessions).claim(MESSAGE_ID))
    with sessions() as session:
        assert session.scalars(select(WhatsAppEventReceipt)).all() == []


def test_unclaimed_completion_rolls_back_and_failed_work_can_retry(
    sessions: sessionmaker[Session],
) -> None:
    identity_store = store(sessions)

    async def run() -> None:
        with pytest.raises(IdempotencyStoreError):
            await identity_store.mark_processed(MESSAGE_ID)
        assert await identity_store.claim(MESSAGE_ID)
        await identity_store.release(MESSAGE_ID)
        assert await store(sessions).claim(MESSAGE_ID)

    asyncio.run(run())


class SlowChat:
    def __init__(self) -> None:
        self.calls = 0

    async def answer(self, message: str) -> str:
        self.calls += 1
        await asyncio.sleep(0.01)
        return "respuesta simulada"


class FailingChat:
    async def answer(self, message: str) -> str:
        raise AIProviderRateLimitError("test-only-provider-error")


class RecordingSender:
    def __init__(self, *, uncertain_failure: bool = False) -> None:
        self.calls = 0
        self.uncertain_failure = uncertain_failure

    async def send_text(self, recipient: str, text: str, *, preview_url: bool = False) -> str:
        self.calls += 1
        if self.uncertain_failure:
            raise WhatsAppProviderTimeoutError("test-only-uncertain-send")
        return "test-only-sent-id"


def inbound() -> InboundMessage:
    return InboundMessage(
        external_message_id=MESSAGE_ID,
        sender_id="5215550000001@c.us",
        text="¿y el rib eye?",
    )


def test_concurrent_duplicate_messages_send_once(sessions: sessionmaker[Session]) -> None:
    chat = SlowChat()
    sender = RecordingSender()
    orchestrators = [MessageOrchestrator(chat, sender, store(sessions)) for _ in range(2)]

    async def race() -> list[bool]:
        return list(
            await asyncio.gather(*(item.process_message(inbound()) for item in orchestrators))
        )

    assert sorted(asyncio.run(race())) == [False, True]
    assert chat.calls == 1
    assert sender.calls == 1
    with sessions() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        assert receipt is not None
        assert receipt.status == "completed"


def test_failure_before_send_releases_receipt_for_later_delivery(
    sessions: sessionmaker[Session],
) -> None:
    sender = RecordingSender()

    async def run() -> None:
        with pytest.raises(MessageProcessingError):
            await MessageOrchestrator(FailingChat(), sender, store(sessions)).process_message(
                inbound()
            )
        assert await MessageOrchestrator(SlowChat(), sender, store(sessions)).process_message(
            inbound()
        )

    asyncio.run(run())
    assert sender.calls == 1
    with sessions() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        assert receipt is not None
        assert receipt.status == "completed"


def test_uncertain_send_keeps_claim_and_blocks_automatic_second_send(
    sessions: sessionmaker[Session],
) -> None:
    sender = RecordingSender(uncertain_failure=True)
    orchestrator = MessageOrchestrator(SlowChat(), sender, store(sessions))

    async def run() -> None:
        with pytest.raises(MessageProcessingError):
            await orchestrator.process_message(inbound())
        assert not await MessageOrchestrator(SlowChat(), sender, store(sessions)).process_message(
            inbound()
        )

    asyncio.run(run())
    assert sender.calls == 1
    with sessions() as session:
        receipt = session.scalar(select(WhatsAppEventReceipt))
        assert receipt is not None
        assert receipt.status == "claimed"
