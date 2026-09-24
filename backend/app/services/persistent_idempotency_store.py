"""Transactional, branch-scoped deduplication of incoming WhatsApp message IDs."""

import asyncio
from datetime import UTC, datetime

from sqlalchemy import delete, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.exceptions import IdempotencyStoreError
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService


class PersistentIdempotencyStore:
    """Use a database uniqueness constraint as the cross-process claim boundary."""

    def __init__(
        self, session_factory: sessionmaker[Session], *, branch_scope: BranchScope
    ) -> None:
        self._session_factory = session_factory
        self._branch_scope = branch_scope

    async def claim(self, message_id: str) -> bool:
        self._validate_message_id(message_id)
        return await asyncio.to_thread(self._claim, message_id)

    async def mark_processed(self, message_id: str) -> None:
        self._validate_message_id(message_id)
        await asyncio.to_thread(self._mark_processed, message_id)

    async def release(self, message_id: str) -> None:
        self._validate_message_id(message_id)
        await asyncio.to_thread(self._release, message_id)

    def _branch_id(self, session: Session) -> int:
        return (
            BranchService(
                BranchRepository(session),
                assistant_branch_code=self._branch_scope.branch_code,
            )
            .get_current_branch()
            .id
        )

    def _claim(self, message_id: str) -> bool:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                result = session.execute(
                    insert(WhatsAppEventReceipt)
                    .values(branch_id=branch_id, provider_message_id=message_id, status="claimed")
                    .on_conflict_do_nothing(index_elements=["branch_id", "provider_message_id"])
                )
                return result.rowcount == 1
        except SQLAlchemyError:
            raise IdempotencyStoreError("could not claim inbound message") from None

    def _mark_processed(self, message_id: str) -> None:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                result = session.execute(
                    update(WhatsAppEventReceipt)
                    .where(
                        WhatsAppEventReceipt.branch_id == branch_id,
                        WhatsAppEventReceipt.provider_message_id == message_id,
                        WhatsAppEventReceipt.status == "claimed",
                    )
                    .values(status="completed", completed_at=datetime.now(UTC))
                )
                if result.rowcount != 1:
                    raise IdempotencyStoreError("cannot complete an unclaimed message id")
        except SQLAlchemyError:
            raise IdempotencyStoreError("could not complete inbound message") from None

    def _release(self, message_id: str) -> None:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                session.execute(
                    delete(WhatsAppEventReceipt).where(
                        WhatsAppEventReceipt.branch_id == branch_id,
                        WhatsAppEventReceipt.provider_message_id == message_id,
                        WhatsAppEventReceipt.status == "claimed",
                    )
                )
        except SQLAlchemyError:
            raise IdempotencyStoreError("could not release inbound message") from None

    @staticmethod
    def _validate_message_id(message_id: str) -> None:
        if (
            not isinstance(message_id, str)
            or not 1 <= len(message_id) <= 512
            or message_id != message_id.strip()
            or not message_id.isprintable()
        ):
            raise IdempotencyStoreError("inbound message id has an invalid format")
