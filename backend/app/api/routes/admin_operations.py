"""Owner-only view of process-local operational counters; no customer identifiers."""

from typing import Annotated

from fastapi import APIRouter, Depends, Response

from backend.app.api.admin_authorization import require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.observability import get_operational_metrics
from backend.app.services.admin_auth_service import AdminSessionInfo

router = APIRouter(prefix="/api/v1/admin/operations", tags=["admin-operations"])


@router.get("/metrics")
def get_metrics(
    response: Response,
    _principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.AUDIT_READ))
    ],
) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    return get_operational_metrics().snapshot()
