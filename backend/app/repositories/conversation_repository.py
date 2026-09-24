"""Conversation persistence constrained to one backend-resolved branch."""

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation


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
        conversation = self._session.scalar(
            select(Conversation).where(
                Conversation.branch_id == self._branch.id,
                Conversation.channel == "whatsapp",
                Conversation.external_user_key == external_user_key,
            )
        )
        assert conversation is not None
        return conversation, result.rowcount == 1
