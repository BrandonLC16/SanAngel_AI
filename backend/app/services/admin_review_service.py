"""Branch-scoped admin review of minimal conversation and unresolved FAQ metadata."""

import hmac
import re
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime, time

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AdminAuthSettings, ConversationIdentitySettings
from backend.app.core.conversation_mode import ConversationMode
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    AdminCommercialConflictError,
    AdminCommercialNotFoundError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from backend.app.db.models.admin_commercial import AdminCommercialAudit, ManagedFAQ
from backend.app.db.models.admin_user import AdminUser
from backend.app.db.models.branch import Branch
from backend.app.db.models.conversation import Conversation
from backend.app.db.models.conversation_responder_state import ConversationResponderState
from backend.app.db.models.manual_send_receipt import ManualSendReceipt
from backend.app.db.models.message import Message
from backend.app.db.models.unresolved_question import UnresolvedQuestion
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.admin_review import (
    ConversationDetail,
    ConversationItem,
    ConversationPage,
    ManualSendSummary,
    MessageMetadata,
    ResolveFAQRequest,
    ResolveFAQResult,
    UnresolvedItem,
    UnresolvedPage,
)
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService
from backend.app.services.faq_service import normalize_faq_question
from backend.app.services.unresolved_question_service import UnresolvedQuestionService

MAX_PAGE_SIZE = 100
MAX_OFFSET = 5000
MAX_DETAIL_MESSAGES = 50
EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)\+?\d[\d\s().-]{7,}\d(?!\d)")


class AdminReviewService:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        *,
        admin_settings: AdminAuthSettings,
        identity_settings: ConversationIdentitySettings,
    ) -> None:
        self._sessions = sessions
        self._scope = BranchScope.from_settings(admin_settings)
        if identity_settings.assistant_branch_code != self._scope.branch_code:
            raise ServiceUnavailableError("admin review branch configuration differs")
        self._identity_settings = identity_settings

    @contextmanager
    def _context(
        self, principal: AdminSessionInfo, permission: AdminPermission
    ) -> Iterator[tuple[Session, Branch]]:
        try:
            with self._sessions.begin() as session:
                branch = BranchService(
                    BranchRepository(session), assistant_branch_code=self._scope.branch_code
                ).get_current_branch()
                if branch.id != principal.branch_id:
                    raise AdminAuthorizationError()
                role = session.scalar(
                    select(AdminUser.role).where(
                        AdminUser.id == principal.user_id,
                        AdminUser.branch_id == branch.id,
                        AdminUser.is_active.is_(True),
                    )
                )
                if role is None or not permits(AdminRole(role), permission):
                    raise AdminAuthorizationError()
                yield session, branch
        except IntegrityError:
            raise AdminCommercialConflictError() from None
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin review persistence failed") from None

    @staticmethod
    def _page(limit: int, offset: int) -> None:
        if type(limit) is not int or not 1 <= limit <= MAX_PAGE_SIZE:
            raise InvalidRequestError()
        if type(offset) is not int or not 0 <= offset <= MAX_OFFSET:
            raise InvalidRequestError()

    @staticmethod
    def _conversation_item(
        row: Conversation, state: ConversationResponderState | None, user_id: int
    ) -> ConversationItem:
        return ConversationItem(
            id=row.id,
            channel=row.channel,
            created_at=row.created_at,
            updated_at=row.updated_at,
            mode=state.mode if state is not None else ConversationMode.AI,
            assigned_to_me=state is not None and state.assigned_admin_user_id == user_id,
        )

    @staticmethod
    def _unresolved_item(row: UnresolvedQuestion) -> UnresolvedItem:
        return UnresolvedItem(
            id=row.id,
            reason=row.reason,
            occurrences=row.occurrences,
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
        )

    def list_conversations(
        self,
        principal: AdminSessionInfo,
        *,
        updated_from: date | None = None,
        updated_to: date | None = None,
        mode: ConversationMode | None = None,
        mine: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> ConversationPage:
        self._page(limit, offset)
        if updated_from and updated_to and updated_from > updated_to:
            raise InvalidRequestError()
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            query = (
                select(Conversation, ConversationResponderState)
                .outerjoin(
                    ConversationResponderState,
                    ConversationResponderState.conversation_id == Conversation.id,
                )
                .where(Conversation.branch_id == branch.id)
            )
            if mode is not None:
                query = query.where(
                    func.coalesce(ConversationResponderState.mode, ConversationMode.AI.value)
                    == mode.value
                )
            if mine:
                query = query.where(
                    ConversationResponderState.assigned_admin_user_id == principal.user_id
                )
            if updated_from is not None:
                query = query.where(
                    Conversation.updated_at >= datetime.combine(updated_from, time.min)
                )
            if updated_to is not None:
                query = query.where(
                    Conversation.updated_at <= datetime.combine(updated_to, time.max)
                )
            rows = session.execute(
                query.order_by(Conversation.updated_at.desc(), Conversation.id.desc())
                .offset(offset)
                .limit(limit + 1)
            ).all()
            return ConversationPage(
                items=[
                    self._conversation_item(row, state, principal.user_id)
                    for row, state in rows[:limit]
                ],
                has_more=len(rows) > limit and offset + limit <= MAX_OFFSET,
            )

    def get_conversation(
        self, principal: AdminSessionInfo, conversation_id: int
    ) -> ConversationDetail:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            row = session.scalar(
                select(Conversation).where(
                    Conversation.id == conversation_id, Conversation.branch_id == branch.id
                )
            )
            if row is None:
                raise AdminCommercialNotFoundError()
            state = session.get(ConversationResponderState, row.id)
            latest_send = session.scalar(
                select(ManualSendReceipt)
                .where(
                    ManualSendReceipt.branch_id == branch.id,
                    ManualSendReceipt.conversation_id == row.id,
                )
                .order_by(ManualSendReceipt.id.desc())
                .limit(1)
            )
            count = (
                session.scalar(
                    select(func.count(Message.id)).where(
                        Message.branch_id == branch.id, Message.conversation_id == row.id
                    )
                )
                or 0
            )
            messages = session.scalars(
                select(Message)
                .where(Message.branch_id == branch.id, Message.conversation_id == row.id)
                .order_by(Message.occurred_at.desc(), Message.id.desc())
                .limit(MAX_DETAIL_MESSAGES)
            ).all()
            return ConversationDetail(
                **self._conversation_item(row, state, principal.user_id).model_dump(),
                message_count=count,
                manual_send_blocked=state.manual_send_blocked if state is not None else False,
                latest_manual_send=(
                    ManualSendSummary(
                        receipt_id=latest_send.id,
                        status=latest_send.status,
                        created_at=latest_send.created_at,
                    )
                    if latest_send is not None
                    else None
                ),
                recent_messages=[
                    MessageMetadata(direction=item.direction, occurred_at=item.occurred_at)
                    for item in messages
                ],
            )

    def list_unresolved(
        self,
        principal: AdminSessionInfo,
        *,
        reason: str | None = None,
        min_occurrences: int = 1,
        limit: int = 50,
        offset: int = 0,
    ) -> UnresolvedPage:
        self._page(limit, offset)
        if (
            reason not in {None, "faq_unknown", "faq_ambiguous"}
            or not 1 <= min_occurrences <= 1000000
        ):
            raise InvalidRequestError()
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            query = select(UnresolvedQuestion).where(
                UnresolvedQuestion.branch_id == branch.id,
                UnresolvedQuestion.occurrences >= min_occurrences,
            )
            if reason is not None:
                query = query.where(UnresolvedQuestion.reason == reason)
            rows = session.scalars(
                query.order_by(
                    UnresolvedQuestion.occurrences.desc(),
                    UnresolvedQuestion.last_seen_at.desc(),
                    UnresolvedQuestion.id.desc(),
                )
                .offset(offset)
                .limit(limit + 1)
            ).all()
            return UnresolvedPage(
                items=[self._unresolved_item(row) for row in rows[:limit]],
                has_more=len(rows) > limit and offset + limit <= MAX_OFFSET,
            )

    def get_unresolved(self, principal: AdminSessionInfo, unresolved_id: int) -> UnresolvedItem:
        with self._context(principal, AdminPermission.COMMERCIAL_READ) as (session, branch):
            row = session.scalar(
                select(UnresolvedQuestion).where(
                    UnresolvedQuestion.id == unresolved_id,
                    UnresolvedQuestion.branch_id == branch.id,
                )
            )
            if row is None:
                raise AdminCommercialNotFoundError()
            return self._unresolved_item(row)

    def resolve_faq(
        self, principal: AdminSessionInfo, unresolved_id: int, payload: ResolveFAQRequest
    ) -> ResolveFAQResult:
        question = payload.question
        if any(
            pattern.search(text)
            for text in (question, payload.answer)
            for pattern in (EMAIL_PATTERN, PHONE_PATTERN)
        ):
            raise InvalidRequestError("FAQ contains likely personal data")
        with self._context(principal, AdminPermission.COMMERCIAL_WRITE) as (session, branch):
            unresolved = session.scalar(
                select(UnresolvedQuestion).where(
                    UnresolvedQuestion.id == unresolved_id,
                    UnresolvedQuestion.branch_id == branch.id,
                )
            )
            if unresolved is None:
                raise AdminCommercialNotFoundError()
            key = UnresolvedQuestionService(session, settings=self._identity_settings).question_key(
                question
            )
            if not hmac.compare_digest(unresolved.question_key, key):
                raise AdminCommercialConflictError("question does not match unresolved aggregate")
            normalized = normalize_faq_question(question)
            faq = session.scalar(
                select(ManagedFAQ).where(
                    ManagedFAQ.branch_id == branch.id, ManagedFAQ.question_key == normalized
                )
            )
            action = "create" if faq is None else "update"
            if faq is None:
                faq = ManagedFAQ(branch_id=branch.id, question_key=normalized)
                session.add(faq)
            faq.category = payload.category.value
            faq.question = question
            faq.answer = payload.answer
            faq.is_active = True
            session.flush()
            session.add(
                AdminCommercialAudit(
                    branch_id=branch.id,
                    actor_user_id=principal.user_id,
                    resource="faq",
                    resource_id=faq.id,
                    action=action,
                )
            )
            try:
                session.flush()
            except SQLAlchemyError:
                raise ServiceUnavailableError("FAQ resolution audit failed") from None
            session.delete(unresolved)
            return ResolveFAQResult(faq_id=faq.id, unresolved_id=unresolved.id)
