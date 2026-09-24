"""Branch-scoped administrative identity and role management endpoints."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response

from backend.app.api.admin_authorization import require_admin_csrf, require_permission
from backend.app.api.routes.admin_auth import COOKIE_NAME, get_admin_auth_service
from backend.app.core.admin_roles import AdminPermission
from backend.app.schemas.admin_auth import (
    AdminProfileResponse,
    AdminRoleChangeRequest,
    AdminUserResponse,
)
from backend.app.services.admin_auth_service import AdminAuthService, AdminSessionInfo

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


@router.get("/me", response_model=AdminProfileResponse)
async def me(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.PROFILE_READ))
    ],
) -> AdminProfileResponse:
    response.headers["Cache-Control"] = "no-store"
    return AdminProfileResponse(username=principal.username, role=principal.role)


@router.get("/users", response_model=list[AdminUserResponse])
async def list_users(
    request: Request,
    response: Response,
    _principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.USERS_READ))
    ],
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> list[AdminUserResponse]:
    users = await asyncio.to_thread(service.list_users, request.cookies.get(COOKIE_NAME))
    response.headers["Cache-Control"] = "no-store"
    return [AdminUserResponse.model_validate(user, from_attributes=True) for user in users]


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def change_role(
    user_id: int,
    payload: AdminRoleChangeRequest,
    request: Request,
    response: Response,
    _principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.USERS_ROLE_WRITE))
    ],
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
    csrf_token: Annotated[str, Depends(require_admin_csrf)],
) -> AdminUserResponse:
    user = await asyncio.to_thread(
        service.change_role,
        request.cookies.get(COOKIE_NAME),
        csrf_token,
        user_id,
        payload.role,
    )
    response.headers["Cache-Control"] = "no-store"
    return AdminUserResponse.model_validate(user, from_attributes=True)
