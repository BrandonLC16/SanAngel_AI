"""Resolve administrator permissions from the current backend session on every request."""

import asyncio
import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, Request

from backend.app.api.routes.admin_auth import (
    COOKIE_NAME,
    get_admin_auth_service,
    require_admin_https,
)
from backend.app.core.admin_roles import AdminPermission, permits
from backend.app.core.exceptions import AdminAuthorizationError, AdminCsrfError
from backend.app.services.admin_auth_service import AdminAuthService, AdminSessionInfo


async def get_current_admin(
    request: Request,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminSessionInfo:
    require_admin_https(request)
    return await asyncio.to_thread(service.get_session, request.cookies.get(COOKIE_NAME))


def require_permission(permission: AdminPermission) -> Callable[..., AdminSessionInfo]:
    async def check(
        principal: Annotated[AdminSessionInfo, Depends(get_current_admin)],
    ) -> AdminSessionInfo:
        if not permits(principal.role, permission):
            raise AdminAuthorizationError()
        return principal

    return check


def require_admin_csrf(
    principal: Annotated[AdminSessionInfo, Depends(get_current_admin)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> str:
    if not isinstance(csrf_token, str) or not hmac.compare_digest(csrf_token, principal.csrf_token):
        raise AdminCsrfError()
    return csrf_token
