"""Branch-scoped SQLite inbox committed before a GreenAPI webhook is acknowledged."""

import asyncio
import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime

from cryptography.fernet import Fernet, InvalidToken
from pydantic import ValidationError
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import ConversationIdentitySettings
from backend.app.core.exceptions import BranchScopeMismatchError, ServiceUnavailableError
from backend.app.db.models.whatsapp_event_receipt import WhatsAppEventReceipt
from backend.app.db.models.whatsapp_inbound_job import WhatsAppInboundJob
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.whatsapp import InboundMessage
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService

MAX_PENDING_JOBS = 5_000


@dataclass(frozen=True)
class ClaimedInboundJob:
    id: int
    message: InboundMessage


class PersistentInboundQueue:
    """Store only encrypted pending work; leave interrupted sends for review."""

    def __init__(
        self,
        session_factory: sessionmaker[Session],
        *,
        branch_scope: BranchScope,
        identity_settings: ConversationIdentitySettings,
    ) -> None:
        if branch_scope.branch_code != identity_settings.assistant_branch_code:
            raise BranchScopeMismatchError("queue identity does not match installation")
        self._session_factory = session_factory
        self._branch_scope = branch_scope
        key = identity_settings.conversation_identity_key.get_secret_value().encode("ascii")
        self._identity_key = key
        subkey = hmac.new(key, b"whatsapp-inbound-queue:v1", hashlib.sha256).digest()
        self._cipher = Fernet(base64.urlsafe_b64encode(subkey))

    async def enqueue(self, messages: tuple[InboundMessage, ...]) -> int:
        return await asyncio.to_thread(self._enqueue, messages)

    async def claim_next(self) -> ClaimedInboundJob | None:
        return await asyncio.to_thread(self._claim_next)

    async def complete(self, job_id: int) -> None:
        await asyncio.to_thread(self._complete, job_id)

    async def mark_uncertain(self, job_id: int) -> None:
        await asyncio.to_thread(self._mark_uncertain, job_id)

    async def counts(self) -> dict[str, int]:
        return await asyncio.to_thread(self._counts)

    def _branch_id(self, session: Session) -> int:
        return (
            BranchService(
                BranchRepository(session), assistant_branch_code=self._branch_scope.branch_code
            )
            .get_current_branch()
            .id
        )

    def _encrypt(self, message: InboundMessage) -> str:
        plaintext = f"{self._branch_scope.branch_code}\n{message.model_dump_json()}".encode()
        return self._cipher.encrypt(plaintext).decode("ascii")

    def _decrypt(self, ciphertext: str, message_id: str) -> InboundMessage:
        try:
            plaintext = self._cipher.decrypt(ciphertext.encode("ascii")).decode("utf-8")
            branch_code, serialized = plaintext.split("\n", 1)
            message = InboundMessage.model_validate_json(serialized)
        except (InvalidToken, UnicodeError, ValueError, ValidationError):
            raise ServiceUnavailableError("queued message cannot be decrypted") from None
        if (
            branch_code != self._branch_scope.branch_code
            or message.external_message_id != message_id
        ):
            raise ServiceUnavailableError("queued message scope mismatch")
        return message

    def _enqueue(self, messages: tuple[InboundMessage, ...]) -> int:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                count = (
                    session.scalar(
                        select(func.count())
                        .select_from(WhatsAppInboundJob)
                        .where(WhatsAppInboundJob.branch_id == branch_id)
                    )
                    or 0
                )
                accepted = 0
                for message in messages:
                    message_id = message.external_message_id
                    existing = session.scalar(
                        select(WhatsAppInboundJob.id).where(
                            WhatsAppInboundJob.branch_id == branch_id,
                            WhatsAppInboundJob.provider_message_id == message_id,
                        )
                    )
                    processed = session.scalar(
                        select(WhatsAppEventReceipt.id).where(
                            WhatsAppEventReceipt.branch_id == branch_id,
                            WhatsAppEventReceipt.provider_message_id == message_id,
                        )
                    )
                    if existing is not None or processed is not None:
                        continue
                    if count >= MAX_PENDING_JOBS:
                        raise ServiceUnavailableError("inbound queue is full")
                    session.add(
                        WhatsAppInboundJob(
                            branch_id=branch_id,
                            provider_message_id=message_id,
                            sender_key=hmac.new(
                                self._identity_key,
                                f"whatsapp:{message.sender_id}".encode(),
                                hashlib.sha256,
                            ).hexdigest(),
                            payload_ciphertext=self._encrypt(message),
                            status="pending",
                        )
                    )
                    session.flush()
                    count += 1
                    accepted += 1
                return accepted
        except SQLAlchemyError:
            raise ServiceUnavailableError("inbound queue could not accept message") from None

    def _claim_next(self) -> ClaimedInboundJob | None:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                next_id = (
                    select(WhatsAppInboundJob.id)
                    .where(
                        WhatsAppInboundJob.branch_id == branch_id,
                        WhatsAppInboundJob.status == "pending",
                    )
                    .order_by(WhatsAppInboundJob.id)
                    .limit(1)
                    .scalar_subquery()
                )
                row = session.execute(
                    update(WhatsAppInboundJob)
                    .where(
                        WhatsAppInboundJob.id == next_id,
                        WhatsAppInboundJob.branch_id == branch_id,
                        WhatsAppInboundJob.status == "pending",
                    )
                    .values(status="processing", claimed_at=datetime.now(UTC))
                    .returning(
                        WhatsAppInboundJob.id,
                        WhatsAppInboundJob.provider_message_id,
                        WhatsAppInboundJob.payload_ciphertext,
                    )
                ).first()
            if row is None:
                return None
            try:
                message = self._decrypt(row.payload_ciphertext, row.provider_message_id)
            except ServiceUnavailableError:
                self._mark_uncertain(row.id)
                raise
            return ClaimedInboundJob(row.id, message)
        except SQLAlchemyError:
            raise ServiceUnavailableError("inbound queue could not claim message") from None

    def _complete(self, job_id: int) -> None:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                result = session.execute(
                    delete(WhatsAppInboundJob).where(
                        WhatsAppInboundJob.id == job_id,
                        WhatsAppInboundJob.branch_id == branch_id,
                        WhatsAppInboundJob.status == "processing",
                    )
                )
                if result.rowcount != 1:
                    raise ServiceUnavailableError("inbound job is not processing")
        except SQLAlchemyError:
            raise ServiceUnavailableError("inbound queue could not complete message") from None

    def _mark_uncertain(self, job_id: int) -> None:
        try:
            with self._session_factory.begin() as session:
                branch_id = self._branch_id(session)
                session.execute(
                    update(WhatsAppInboundJob)
                    .where(
                        WhatsAppInboundJob.id == job_id,
                        WhatsAppInboundJob.branch_id == branch_id,
                        WhatsAppInboundJob.status == "processing",
                    )
                    .values(status="uncertain")
                )
        except SQLAlchemyError:
            raise ServiceUnavailableError("inbound queue could not mark uncertainty") from None

    def _counts(self) -> dict[str, int]:
        try:
            with self._session_factory() as session:
                branch_id = self._branch_id(session)
                rows = session.execute(
                    select(WhatsAppInboundJob.status, func.count())
                    .where(WhatsAppInboundJob.branch_id == branch_id)
                    .group_by(WhatsAppInboundJob.status)
                )
                counts = {status: count for status, count in rows}
                return {
                    status: counts.get(status, 0)
                    for status in ("pending", "processing", "uncertain")
                }
        except SQLAlchemyError:
            raise ServiceUnavailableError("inbound queue status unavailable") from None
