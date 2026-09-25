"""Conversation persistence constrained to one backend-resolved branch."""

from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState


class ConversationRepository:
    def __init__(self, session: Session, *, branch: Branch) -> None:
        self._session = session
        self._branch = branch

    def get_or_create(self, external_user_key: str) -> tuple[Conversation, bool]:
        result = self._session.execute(
            insert(Conversation)
            .values(
                branch_id=self._branch.id,
                channel="whatsapp",
                external_user_key=external_user_key,
            )
            .on_conflict_do_nothing(index_elements=["branch_id", "channel", "external_user_key"])
        )
        self._session.execute(
            update(Conversation)
            .where(
                Conversation.branch_id == self._branch.id,
                Conversation.channel == "whatsapp",
                Conversation.external_user_key == external_user_key,
            )
            .values(updated_at=datetime.now(UTC))
        )
        conversation = self._session.scalar(
            select(Conversation).where(
                Conversation.branch_id == self._branch.id,
                Conversation.channel == "whatsapp",
                Conversation.external_user_key == external_user_key,
            )
        )
        assert conversation is not None
        self._session.execute(
            insert(ConversationResponderState)
            .values(conversation_id=conversation.id, branch_id=self._branch.id)
            .on_conflict_do_nothing(index_elements=["conversation_id"])
        )
        return conversation, result.rowcount == 1
