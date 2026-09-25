"""Read-only administrative audit trail, restricted to the configured branch."""

import asyncio
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from backend.app.api.admin_authorization import require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.config import get_admin_auth_settings
from backend.app.db.session import get_database_session_factory
from backend.app.schemas.admin_audit import AuditPage
from backend.app.services.admin_audit_service import AdminAuditService
from backend.app.services.admin_auth_service import AdminSessionInfo

router = APIRouter(prefix="/api/v1/admin/audit", tags=["admin-audit"])


def get_admin_audit_service() -> AdminAuditService:
    return AdminAuditService(get_database_session_factory(), settings=get_admin_auth_settings())


@router.get("/events", response_model=AuditPage)
async def list_audit_events(
    response: Response,
    principal: Annotated[AdminSessionInfo, Depends(require_permission(AdminPermission.AUDIT_READ))],
    service: Annotated[AdminAuditService, Depends(get_admin_audit_service)],
    entity: Literal["branch", "product", "price", "faq", "admin_user"] | None = None,
    product_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> AuditPage:
    page = await asyncio.to_thread(
        service.list_events,
        principal,
        entity=entity,
        product_id=product_id,
        limit=limit,
        offset=offset,
    )
    response.headers["Cache-Control"] = "no-store"
    return page
