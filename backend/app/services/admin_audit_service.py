"""Read scoped administrative receipts through a fixed, safe projection."""

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.admin_roles import AdminPermission, AdminRole, permits
from backend.app.core.config import AdminAuthSettings
from backend.app.core.exceptions import (
    AdminAuthorizationError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from backend.app.db.models.admin_commercial import AdminCommercialAudit
from backend.app.db.models.admin_user import AdminRoleAudit, AdminUser
from backend.app.repositories.branch_repository import BranchRepository
from backend.app.schemas.admin_audit import AuditEvent, AuditPage
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.branch_scope import BranchScope
from backend.app.services.branch_service import BranchService


def _utc(value: datetime) -> datetime:
    return value.replace(tzinfo=UTC) if value.tzinfo is None else value.astimezone(UTC)


class AdminAuditService:
    def __init__(self, sessions: sessionmaker[Session], *, settings: AdminAuthSettings) -> None:
        self._sessions = sessions
        self._scope = BranchScope.from_settings(settings)

    def list_events(
        self,
        principal: AdminSessionInfo,
        *,
        limit: int,
        offset: int,
        entity: str | None = None,
        product_id: int | None = None,
    ) -> AuditPage:
        if product_id is not None and entity != "price":
            raise InvalidRequestError("product filter requires price entity")
        try:
            with self._sessions() as session:
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
                if role is None or not permits(AdminRole(role), AdminPermission.AUDIT_READ):
                    raise AdminAuthorizationError()

                fetch_count = offset + limit + 1
                commercial = select(AdminCommercialAudit).where(
                    AdminCommercialAudit.branch_id == branch.id
                )
                if entity is not None:
                    commercial = commercial.where(AdminCommercialAudit.resource == entity)
                if product_id is not None:
                    commercial = commercial.where(
                        AdminCommercialAudit.resource == "price",
                        AdminCommercialAudit.product_id == product_id,
                    )
                commercial = commercial.order_by(
                    AdminCommercialAudit.changed_at.desc(), AdminCommercialAudit.id.desc()
                ).limit(fetch_count)
                events = [
                    AuditEvent(
                        id=row.id,
                        source="commercial",
                        actor_user_id=row.actor_user_id,
                        action=row.action,
                        entity=row.resource,
                        entity_id=row.resource_id,
                        occurred_at=_utc(row.changed_at),
                        product_id=row.product_id if row.resource == "price" else None,
                        unit=row.unit if row.resource == "price" else None,
                        before={"amount": str(row.old_amount)}
                        if row.resource == "price" and row.old_amount is not None
                        else None,
                        after={"amount": str(row.new_amount)}
                        if row.resource == "price" and row.new_amount is not None
                        else None,
                    )
                    for row in session.scalars(commercial)
                ]
                if entity in (None, "admin_user") and product_id is None:
                    roles = (
                        select(AdminRoleAudit)
                        .where(AdminRoleAudit.branch_id == branch.id)
                        .order_by(AdminRoleAudit.changed_at.desc(), AdminRoleAudit.id.desc())
                        .limit(fetch_count)
                    )
                    events.extend(
                        AuditEvent(
                            id=row.id,
                            source="role",
                            actor_user_id=row.actor_user_id,
                            action="update",
                            entity="admin_user",
                            entity_id=row.target_user_id,
                            occurred_at=_utc(row.changed_at),
                            before={"role": row.old_role},
                            after={"role": row.new_role},
                        )
                        for row in session.scalars(roles)
                    )
                events.sort(key=lambda item: (item.occurred_at, item.source, item.id), reverse=True)
                page = events[offset : offset + limit + 1]
                return AuditPage(items=page[:limit], has_more=len(page) > limit)
        except SQLAlchemyError:
            raise ServiceUnavailableError("admin audit persistence failed") from None
