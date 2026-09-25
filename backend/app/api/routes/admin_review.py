"""Admin-only minimal conversation and unresolved FAQ review routes."""

import asyncio
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from backend.app.api.admin_authorization import require_admin_csrf, require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.config import get_admin_auth_settings, get_conversation_identity_settings
from backend.app.core.conversation_mode import ConversationMode
from backend.app.db.session import get_database_session_factory
from backend.app.schemas.admin_review import (
    ConversationDetail,
    ConversationModeResult,
    ConversationPage,
    ResolveFAQRequest,
    ResolveFAQResult,
    UnresolvedItem,
    UnresolvedPage,
)
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.admin_review_service import AdminReviewService
from backend.app.services.conversation_mode_service import ConversationModeService

router = APIRouter(prefix="/api/v1/admin/review", tags=["admin-review"])


def get_admin_review_service() -> AdminReviewService:
    return AdminReviewService(
        get_database_session_factory(),
        admin_settings=get_admin_auth_settings(),
        identity_settings=get_conversation_identity_settings(),
    )


def get_conversation_mode_service() -> ConversationModeService:
    return ConversationModeService(
        get_database_session_factory(), settings=get_admin_auth_settings()
    )


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


@router.get("/conversations", response_model=ConversationPage)
async def list_conversations(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
    updated_from: date | None = None,
    updated_to: date | None = None,
    mode: ConversationMode | None = None,
    mine: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> ConversationPage:
    result = await asyncio.to_thread(
        service.list_conversations,
        principal,
        updated_from=updated_from,
        updated_to=updated_to,
        mode=mode,
        mine=mine,
        limit=limit,
        offset=offset,
    )
    _no_store(response)
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
) -> ConversationDetail:
    result = await asyncio.to_thread(service.get_conversation, principal, conversation_id)
    _no_store(response)
    return result


@router.post("/conversations/{conversation_id}/take", response_model=ConversationModeResult)
async def take_conversation(
    conversation_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.CONVERSATION_MODE_WRITE))
    ],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
    service: Annotated[ConversationModeService, Depends(get_conversation_mode_service)],
) -> ConversationModeResult:
    result = await asyncio.to_thread(service.take, principal, conversation_id)
    _no_store(response)
    return ConversationModeResult(mode=result.mode, assigned_to_me=True)


@router.post("/conversations/{conversation_id}/release", response_model=ConversationModeResult)
async def release_conversation(
    conversation_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.CONVERSATION_MODE_WRITE))
    ],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
    service: Annotated[ConversationModeService, Depends(get_conversation_mode_service)],
) -> ConversationModeResult:
    result = await asyncio.to_thread(service.release, principal, conversation_id)
    _no_store(response)
    return ConversationModeResult(mode=result.mode, assigned_to_me=False)


@router.get("/unresolved", response_model=UnresolvedPage)
async def list_unresolved(
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
    reason: Literal["faq_unknown", "faq_ambiguous"] | None = None,
    min_occurrences: Annotated[int, Query(ge=1, le=1000000)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> UnresolvedPage:
    result = await asyncio.to_thread(
        service.list_unresolved,
        principal,
        reason=reason,
        min_occurrences=min_occurrences,
        limit=limit,
        offset=offset,
    )
    _no_store(response)
    return result


@router.get("/unresolved/{unresolved_id}", response_model=UnresolvedItem)
async def get_unresolved(
    unresolved_id: int,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_READ))
    ],
    service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
) -> UnresolvedItem:
    result = await asyncio.to_thread(service.get_unresolved, principal, unresolved_id)
    _no_store(response)
    return result


@router.post("/unresolved/{unresolved_id}/resolve", response_model=ResolveFAQResult)
async def resolve_faq(
    unresolved_id: int,
    payload: ResolveFAQRequest,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    service: Annotated[AdminReviewService, Depends(get_admin_review_service)],
    _csrf: Annotated[str, Depends(require_admin_csrf)],
) -> ResolveFAQResult:
    result = await asyncio.to_thread(service.resolve_faq, principal, unresolved_id, payload)
    _no_store(response)
    return result
