"""Exclusive response ownership, branch scope, and atomic handoff checks."""

import asyncio
from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminRole
from backend.app.core.config import AssistantSettings
from backend.app.core.conversation_mode import ConversationMode
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    ConversationModeConflictError,
    ConversationNotFoundError,
)
from backend.app.db.base import Base
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.session import create_database_engine, create_database_session_factory
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.conversation_mode_service import ConversationModeService


@pytest.fixture
def scenario(
    tmp_path: Path,
) -> Generator[tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int]]:
    engine: Engine = create_database_engine(
        f"sqlite+pysqlite:///{(tmp_path / 'conversation-mode.db').as_posix()}"
    )
    Base.metadata.create_all(engine)
    sessions = create_database_session_factory(engine)
    with sessions.begin() as session:
        own = Branch(code="sucursal-uno", name="Uno", address="Prueba", business_hours="Lunes")
        other = Branch(code="sucursal-dos", name="Dos", address="Prueba", business_hours="Martes")
        session.add_all((own, other))
        session.flush()
        own_conversation = Conversation(branch_id=own.id, external_user_key="a" * 64)
        other_conversation = Conversation(branch_id=other.id, external_user_key="b" * 64)
        session.add_all((own_conversation, other_conversation))
        session.flush()
        users = {
            "editor": AdminUser(
                branch_id=own.id, username="editor", role="editor", password_hash="$argon2id$test"
            ),
            "second": AdminUser(
                branch_id=own.id, username="second", role="editor", password_hash="$argon2id$test"
            ),
            "owner": AdminUser(
                branch_id=own.id, username="owner", role="owner", password_hash="$argon2id$test"
            ),
            "viewer": AdminUser(
                branch_id=own.id, username="viewer", role="viewer", password_hash="$argon2id$test"
            ),
            "foreign": AdminUser(
                branch_id=other.id,
                username="foreign",
                role="owner",
                password_hash="$argon2id$test",
            ),
        }
        session.add_all(users.values())
        session.flush()
        expires_at = datetime.now(UTC) + timedelta(hours=1)
        principals = {
            key: AdminSessionInfo(
                username=user.username,
                expires_at=expires_at,
                csrf_token="test-only-csrf",
                user_id=user.id,
                branch_id=user.branch_id,
                role=AdminRole(user.role),
            )
            for key, user in users.items()
        }
        own_id, other_id = own_conversation.id, other_conversation.id
    try:
        yield sessions, principals, own_id, other_id
    finally:
        engine.dispose()


def service(sessions: sessionmaker[Session]) -> ConversationModeService:
    return ConversationModeService(
        sessions,
        settings=AssistantSettings(assistant_branch_code="sucursal-uno", _env_file=None),
    )


def test_handoff_keeps_one_human_owner_and_blocks_ai_while_assigned(
    scenario: tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int],
) -> None:
    sessions, principals, conversation_id, _ = scenario
    modes = service(sessions)

    assert modes.begin_ai_reply(conversation_id) is True
    with pytest.raises(ConversationModeConflictError):
        modes.take(principals["editor"], conversation_id)
    modes.finish_ai_reply(conversation_id)

    assert modes.take(principals["editor"], conversation_id).mode is ConversationMode.HUMAN
    assert modes.begin_ai_reply(conversation_id) is False
    with pytest.raises(ConversationModeConflictError):
        modes.take(principals["second"], conversation_id)
    with pytest.raises(AdminAuthorizationError):
        modes.release(principals["second"], conversation_id)

    with sessions() as session:
        state = session.get(ConversationResponderState, conversation_id)
        assert state is not None
        assert state.mode == "HUMAN"
        assert state.assigned_admin_user_id == principals["editor"].user_id
        assert state.ai_reply_count == 0

    assert modes.release(principals["owner"], conversation_id).mode is ConversationMode.AI
    assert modes.begin_ai_reply(conversation_id) is True
    modes.finish_ai_reply(conversation_id)


def test_transition_rechecks_role_active_user_expiry_and_branch(
    scenario: tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int],
) -> None:
    sessions, principals, conversation_id, other_conversation_id = scenario
    modes = service(sessions)
    with pytest.raises(AdminAuthorizationError):
        modes.take(principals["viewer"], conversation_id)
    with pytest.raises(AdminAuthorizationError):
        modes.take(principals["foreign"], conversation_id)
    with pytest.raises(ConversationNotFoundError):
        modes.take(principals["editor"], other_conversation_id)

    expired = AdminSessionInfo(
        username="editor",
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
        csrf_token="test-only-csrf",
        user_id=principals["editor"].user_id,
        branch_id=principals["editor"].branch_id,
        role=AdminRole.EDITOR,
    )
    with pytest.raises(AdminAuthorizationError):
        modes.take(expired, conversation_id)

    with sessions.begin() as session:
        editor = session.get(AdminUser, principals["editor"].user_id)
        assert editor is not None
        editor.role = "viewer"
    with pytest.raises(AdminAuthorizationError):
        modes.take(principals["editor"], conversation_id)
    with sessions.begin() as session:
        editor = session.get(AdminUser, principals["editor"].user_id)
        assert editor is not None
        editor.role = "editor"
        editor.is_active = False
    with pytest.raises(AdminAuthorizationError):
        modes.take(principals["editor"], conversation_id)


def test_concurrent_take_has_one_winner(
    scenario: tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int],
) -> None:
    sessions, principals, conversation_id, _ = scenario
    modes = service(sessions)

    def attempt(name: str) -> bool:
        try:
            modes.take(principals[name], conversation_id)
            return True
        except ConversationModeConflictError:
            return False

    async def race() -> list[bool]:
        return await asyncio.gather(
            asyncio.to_thread(attempt, "editor"), asyncio.to_thread(attempt, "second")
        )

    assert sorted(asyncio.run(race())) == [False, True]
    with sessions() as session:
        state = session.scalar(select(ConversationResponderState))
        assert state is not None
        assert state.assigned_admin_user_id in {
            principals["editor"].user_id,
            principals["second"].user_id,
        }


def test_ai_claim_and_human_take_cannot_both_win(
    scenario: tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int],
) -> None:
    sessions, principals, conversation_id, _ = scenario
    modes = service(sessions)

    def take() -> bool:
        try:
            modes.take(principals["editor"], conversation_id)
            return True
        except ConversationModeConflictError:
            return False

    async def race() -> tuple[bool, bool]:
        human, ai = await asyncio.gather(
            asyncio.to_thread(take), asyncio.to_thread(modes.begin_ai_reply, conversation_id)
        )
        return human, ai

    human, ai = asyncio.run(race())
    assert human != ai
    with sessions() as session:
        state = session.get(ConversationResponderState, conversation_id)
        assert state is not None
        assert (state.mode, state.ai_reply_count) == (("HUMAN", 0) if human else ("AI", 1))
    if ai:
        modes.finish_ai_reply(conversation_id)


def test_database_rejects_cross_branch_owner_and_invalid_mode(
    scenario: tuple[sessionmaker[Session], dict[str, AdminSessionInfo], int, int],
) -> None:
    sessions, principals, conversation_id, _ = scenario
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(
                ConversationResponderState(
                    conversation_id=conversation_id,
                    branch_id=principals["editor"].branch_id,
                    mode="HUMAN",
                    assigned_admin_user_id=principals["foreign"].user_id,
                )
            )
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(
                ConversationResponderState(
                    conversation_id=conversation_id,
                    branch_id=principals["editor"].branch_id,
                    mode="HUMAN",
                    assigned_admin_user_id=principals["editor"].user_id,
                    ai_reply_count=1,
                )
            )
    with pytest.raises(IntegrityError):
        with sessions.begin() as session:
            session.add(
                ConversationResponderState(
                    conversation_id=conversation_id,
                    branch_id=principals["editor"].branch_id,
                    mode="operator",
                )
            )
