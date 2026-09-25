"""Branch-scoped, atomic ownership of WhatsApp conversation responses."""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AssistantSettings
from backend.app.core.conversation_mode import ConversationMode
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    ConversationModeConflictError,
    ConversationNotFoundError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService


@dataclass(frozen=True, slots=True)
class ConversationModeState:
    mode: ConversationMode
    assigned_admin_user_id: int | None


class ConversationModeService:
    """Only one human owns HUMAN mode; AI claims block handoff while replies are in flight."""

    def __init__(self, sessions: sessionmaker[Session], *, settings: AssistantSettings) -> None:
        self._sessions = sessions
        self._scope = BranchScope.from_settings(settings)

    def _branch(self, session: Session) -> Branch:
        return BranchService(
            BranchRepository(session), assistant_branch_code=self._scope.branch_code
        ).get_current_branch()

    @staticmethod
    def _conversation_id(value: int) -> int:
        if type(value) is not int or value < 1:
            raise InvalidRequestError("invalid conversation id")
        return value

    @staticmethod
    def _authorize(session: Session, principal: AdminSessionInfo, branch: Branch) -> AdminRole:
        if principal.branch_id != branch.id or principal.expires_at <= datetime.now(UTC):
            raise AdminAuthorizationError()
        role = session.scalar(
            select(AdminUser.role).where(
                AdminUser.id == principal.user_id,
                AdminUser.branch_id == branch.id,
                AdminUser.is_active.is_(True),
            )
        )
        if role is None or not permits(AdminRole(role), AdminPermission.CONVERSATION_MODE_WRITE):
            raise AdminAuthorizationError()
        return AdminRole(role)

    @staticmethod
    def _state_row(
        session: Session, branch_id: int, conversation_id: int
    ) -> ConversationResponderState:
        conversation = session.scalar(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.branch_id == branch_id
            )
        )
        if conversation is None:
            raise ConversationNotFoundError()
        session.execute(
            insert(ConversationResponderState)
            .values(conversation_id=conversation_id, branch_id=branch_id)
            .on_conflict_do_nothing(index_elements=["conversation_id"])
        )
        row = session.get(ConversationResponderState, conversation_id)
        assert row is not None
        return row

    def take(self, principal: AdminSessionInfo, conversation_id: int) -> ConversationModeState:
        """Atomically transfer an idle AI conversation to one current editor or owner."""
        conversation_id = self._conversation_id(conversation_id)
        try:
            with self._sessions.begin() as session:
                branch = self._branch(session)
                self._authorize(session, principal, branch)
                self._state_row(session, branch.id, conversation_id)
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == conversation_id,
                        ConversationResponderState.branch_id == branch.id,
                        ConversationResponderState.mode == ConversationMode.AI.value,
                        ConversationResponderState.ai_reply_count == 0,
                        ConversationResponderState.assigned_admin_user_id.is_(None),
                    )
                    .values(
                        mode=ConversationMode.HUMAN.value,
                        assigned_admin_user_id=principal.user_id,
                    )
                )
                if changed.rowcount != 1:
                    raise ConversationModeConflictError()
                session.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation_id, Conversation.branch_id == branch.id)
                    .values(updated_at=datetime.now(UTC))
                )
            return ConversationModeState(ConversationMode.HUMAN, principal.user_id)
        except SQLAlchemyError:
            raise ServiceUnavailableError("conversation mode handoff failed") from None

    def release(self, principal: AdminSessionInfo, conversation_id: int) -> ConversationModeState:
        """The assignee or an owner may return a human conversation to AI."""
        conversation_id = self._conversation_id(conversation_id)
        try:
            with self._sessions.begin() as session:
                branch = self._branch(session)
                role = self._authorize(session, principal, branch)
                row = self._state_row(session, branch.id, conversation_id)
                if row.mode != ConversationMode.HUMAN.value:
                    raise ConversationModeConflictError()
                if row.assigned_admin_user_id != principal.user_id and role != AdminRole.OWNER:
                    raise AdminAuthorizationError()
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == conversation_id,
                        ConversationResponderState.branch_id == branch.id,
                        ConversationResponderState.mode == ConversationMode.HUMAN.value,
                        ConversationResponderState.assigned_admin_user_id
                        == row.assigned_admin_user_id,
                        ConversationResponderState.ai_reply_count == 0,
                    )
                    .values(
                        mode=ConversationMode.AI.value,
                        assigned_admin_user_id=None,
                    )
                )
                if changed.rowcount != 1:
                    raise ConversationModeConflictError()
                session.execute(
                    update(Conversation)
                    .where(Conversation.id == conversation_id, Conversation.branch_id == branch.id)
                    .values(updated_at=datetime.now(UTC))
                )
            return ConversationModeState(ConversationMode.AI, None)
        except SQLAlchemyError:
            raise ServiceUnavailableError("conversation mode release failed") from None

    def begin_ai_reply(self, conversation_id: int) -> bool:
        """Reserve one AI reply; HUMAN mode refuses it without calling the model."""
        conversation_id = self._conversation_id(conversation_id)
        try:
            with self._sessions.begin() as session:
                branch = self._branch(session)
                self._state_row(session, branch.id, conversation_id)
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == conversation_id,
                        ConversationResponderState.branch_id == branch.id,
                        ConversationResponderState.mode == ConversationMode.AI.value,
                    )
                    .values(ai_reply_count=ConversationResponderState.ai_reply_count + 1)
                )
                if changed.rowcount != 1:
                    return False
            return True
        except SQLAlchemyError:
            raise ServiceUnavailableError("conversation AI claim failed") from None

    def finish_ai_reply(self, conversation_id: int) -> None:
        """Clear a claim after a confirmed send or before any send attempt."""
        conversation_id = self._conversation_id(conversation_id)
        try:
            with self._sessions.begin() as session:
                branch = self._branch(session)
                changed = session.execute(
                    update(ConversationResponderState)
                    .where(
                        ConversationResponderState.conversation_id == conversation_id,
                        ConversationResponderState.branch_id == branch.id,
                        ConversationResponderState.mode == ConversationMode.AI.value,
                        ConversationResponderState.ai_reply_count > 0,
                    )
                    .values(ai_reply_count=ConversationResponderState.ai_reply_count - 1)
                )
                if changed.rowcount != 1:
                    raise ServiceUnavailableError("conversation AI claim missing")
        except SQLAlchemyError:
            raise ServiceUnavailableError("conversation AI claim release failed") from None


class PersistentConversationModeGate:
    """Async adapter for the existing webhook orchestrator."""

    def __init__(self, service: ConversationModeService) -> None:
        self._service = service

    async def begin_ai_reply(self, conversation_id: int) -> bool:
        return await asyncio.to_thread(self._service.begin_ai_reply, conversation_id)

    async def finish_ai_reply(self, conversation_id: int) -> None:
        await asyncio.to_thread(self._service.finish_ai_reply, conversation_id)
