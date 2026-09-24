"""Authentication only; authorization and admin CRUD belong to later subphases."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response

from backend.app.core.config import get_admin_auth_settings
from backend.app.core.exceptions import AdminTransportError
from backend.app.db.session import get_database_session_factory
from backend.app.schemas.admin_auth import AdminLoginRequest, AdminSessionResponse
from backend.app.services.admin_auth_service import (
    SESSION_SECONDS,
    AdminAuthService,
    AdminSessionInfo,
)

COOKIE_NAME = "__Host-admin_session"
router = APIRouter(prefix="/api/v1/admin/auth", tags=["admin-auth"])


def get_admin_auth_service() -> AdminAuthService:
    return AdminAuthService(get_database_session_factory(), settings=get_admin_auth_settings())


def _response_data(session: AdminSessionInfo) -> AdminSessionResponse:
    return AdminSessionResponse(
        username=session.username,
        expires_at=session.expires_at,
        csrf_token=session.csrf_token,
    )


def _require_https(request: Request) -> None:
    if request.url.scheme != "https":
        raise AdminTransportError()


@router.post("/login", response_model=AdminSessionResponse)
async def login(
    payload: AdminLoginRequest,
    request: Request,
    response: Response,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminSessionResponse:
    _require_https(request)
    peer = request.client.host if request.client is not None else "unknown"
    result = await asyncio.to_thread(
        service.login, payload.username, payload.password.get_secret_value(), peer=peer
    )
    response.set_cookie(
        COOKIE_NAME,
        result.token,
        max_age=SESSION_SECONDS,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    response.headers["Cache-Control"] = "no-store"
    return _response_data(result.session)


@router.get("/session", response_model=AdminSessionResponse)
async def session_info(
    request: Request,
    response: Response,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
) -> AdminSessionResponse:
    _require_https(request)
    session = await asyncio.to_thread(service.get_session, request.cookies.get(COOKIE_NAME))
    response.headers["Cache-Control"] = "no-store"
    return _response_data(session)


@router.post("/logout", status_code=204)
async def logout(
    request: Request,
    service: Annotated[AdminAuthService, Depends(get_admin_auth_service)],
    csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None,
) -> Response:
    _require_https(request)
    await asyncio.to_thread(service.logout, request.cookies.get(COOKIE_NAME), csrf_token)
    response = Response(status_code=204, headers={"Cache-Control": "no-store"})
    response.delete_cookie(COOKIE_NAME, path="/", secure=True, httponly=True, samesite="strict")
    return response
