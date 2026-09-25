"""Send one confirmed human reply through this installation's WhatsApp client."""

import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AdminAuthSettings, ConversationIdentitySettings, Settings
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    ConversationModeConflictError,
    ConversationNotFoundError,
    ServiceUnavailableError,
    WhatsAppProviderError,
)
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.manual_send_receipt import ManualSendReceipt
from backend.app.db.models.message import Message
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.conversation_recipient_cipher import ConversationRecipientCipher
from backend.app.services.whatsapp_client import WhatsAppClient


class _Sender(Protocol):
    async def send_text(self, recipient: str, text: str, *, preview_url: bool = False) -> str: ...


@dataclass(frozen=True, slots=True)
class ManualReplyStatus:
    receipt_id: int
    status: str


class ManualReplyService:
    """Reserve before network I/O; never replay a request with an uncertain outcome."""

    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        admin_settings: AdminAuthSettings,
        identity_settings: ConversationIdentitySettings,
        whatsapp_settings: Settings,
        sender_factory: Callable[[], AbstractAsyncContextManager[_Sender]] | None = None,
    ) -> None:
        branch = admin_settings.assistant_branch_code
        if (
            identity_settings.assistant_branch_code != branch
            or whatsapp_settings.assistant_branch_code != branch
        ):
            raise ServiceUnavailableError("manual reply branch configuration differs")
        self._sessions = sessions
        self._scope = BranchScope.from_settings(admin_settings)
        self._cipher = ConversationRecipientCipher(identity_settings)
        self._sender_factory = sender_factory or (lambda: WhatsAppClient(whatsapp_settings))

    def _authorize(self, session: Session, principal: AdminSessionInfo) -> int:
        branch = BranchService(
            BranchRepository(session), assistant_branch_code=self._scope.branch_code
        ).get_current_branch()
        if principal.branch_id != branch.id or principal.expires_at <= datetime.now(UTC):
            raise AdminAuthorizationError()
        role = session.scalar(
            select(AdminUser.role).where(
                AdminUser.id == principal.user_id,
                AdminUser.branch_id == branch.id,
                AdminUser.is_active.is_(True),
            )
        )
        if role is None or not permits(AdminRole(role), AdminPermission.CONVERSATION_SEND):
            raise AdminAuthorizationError()
        return branch.id

    def _reserve(
        self, principal: AdminSessionInfo, conversation_id: int, request_id: UUID
    ) -> tuple[ManualReplyStatus, str | None]:
        try:
            with self._sessions.begin() as session:
                branch_id = self._authorize(session, principal)
                conversation = session.scalar(
                    select(Conversation).where(
                        Conversation.id == conversation_id, Conversation.branch_id == branch_id
                    )
                )
                if conversation is None:
                    raise ConversationNotFoundError()
                state = session.get(ConversationResponderState, conversation_id)
                if (
                    state is None
                    or state.branch_id != branch_id
                    or state.mode != "HUMAN"
                    or state.assigned_admin_user_id != principal.user_id
                ):
                    raise AdminAuthorizationError()
                existing = session.scalar(
                    select(ManualSendReceipt).where(
                        ManualSendReceipt.branch_id == branch_id,
                        ManualSendReceipt.conversation_id == conversation_id,
                        ManualSendReceipt.request_id == str(request_id),
                    )
                )
                if existing is not None:
                    return ManualReplyStatus(existing.id, existing.status), None
                if state.manual_send_blocked:
                    raise ConversationModeConflictError()
                recipient = self._cipher.decrypt(conversation)
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == conversation_id,
                        ConversationResponderState.branch_id == branch_id,
                        ConversationResponderState.mode == "HUMAN",
                        ConversationResponderState.assigned_admin_user_id == principal.user_id,
                        ConversationResponderState.manual_send_blocked.is_(False),
                    )
                    .values(manual_send_blocked=True)
                )
                if changed.rowcount != 1:
                    raise ConversationModeConflictError()
                receipt = ManualSendReceipt(
                    conversation_id=conversation_id,
                    branch_id=branch_id,
                    actor_user_id=principal.user_id,
                    request_id=str(request_id),
                    status="pending",
                )
                session.add(receipt)
                session.flush()
                result = ManualReplyStatus(receipt.id, receipt.status)
            return result, recipient
        except SQLAlchemyError:
            raise ServiceUnavailableError("manual reply reservation failed") from None

    def _finish(self, receipt_id: int, *, provider_message_id: str | None) -> None:
        try:
            with self._sessions.begin() as session:
                receipt = session.get(ManualSendReceipt, receipt_id)
                if receipt is None or receipt.status != "pending":
                    raise ServiceUnavailableError("manual reply receipt changed")
                if provider_message_id is None:
                    receipt.status = "uncertain"
                    return
                receipt.status = "accepted"
                receipt.provider_message_id = provider_message_id
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == receipt.conversation_id,
                        ConversationResponderState.branch_id == receipt.branch_id,
                        ConversationResponderState.mode == "HUMAN",
                        ConversationResponderState.assigned_admin_user_id == receipt.actor_user_id,
                        ConversationResponderState.manual_send_blocked.is_(True),
                    )
                    .values(manual_send_blocked=False)
                )
                if changed.rowcount != 1:
                    raise ServiceUnavailableError("manual reply state changed")
                session.add(
                    Message(
                        branch_id=receipt.branch_id,
                        conversation_id=receipt.conversation_id,
                        direction="outbound",
                    )
                )
                session.execute(
                    update(Conversation)
                    .where(
                        Conversation.id == receipt.conversation_id,
                        Conversation.branch_id == receipt.branch_id,
                    )
                    .values(updated_at=datetime.now(UTC))
                )
        except SQLAlchemyError:
            raise ServiceUnavailableError("manual reply confirmation failed") from None

    async def send(
        self, principal: AdminSessionInfo, conversation_id: int, request_id: UUID, text: str
    ) -> ManualReplyStatus:
        if type(conversation_id) is not int or conversation_id < 1:
            raise ConversationNotFoundError()
        # Build the sender before reserving, so missing provider configuration cannot lock a chat.
        async with self._sender_factory() as sender:
            result, recipient = await asyncio.to_thread(
                self._reserve, principal, conversation_id, request_id
            )
            if recipient is None:
                return result
            try:
                provider_message_id = await sender.send_text(recipient, text)
            except WhatsAppProviderError:
                await asyncio.to_thread(self._finish, result.receipt_id, provider_message_id=None)
                return ManualReplyStatus(result.receipt_id, "uncertain")
        await asyncio.to_thread(
            self._finish, result.receipt_id, provider_message_id=provider_message_id
        )
        return ManualReplyStatus(result.receipt_id, "accepted")
