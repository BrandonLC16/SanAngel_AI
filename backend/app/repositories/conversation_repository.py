"""Conversation persistence constrained to one backend-resolved branch."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation


class ConversationRepository:
    def __init__(self, session: Session, *, branch: Branch) -> None:
        self._session = session
        self._branch = branch

    def get_or_create(self, external_user_key: str) -> tuple[Conversation, bool]:
        conversation = self._session.scalar(
            select(Conversation).where(
                Conversation.branch_id == self._branch.id,
                Conversation.channel == "whatsapp",
                Conversation.external_user_key == external_user_key,
            )
        )
        if conversation is not None:
            return conversation, False

        conversation = Conversation(
            branch_id=self._branch.id,
            channel="whatsapp",
            external_user_key=external_user_key,
        )
        self._session.add(conversation)
        self._session.flush()
        return conversation, True
