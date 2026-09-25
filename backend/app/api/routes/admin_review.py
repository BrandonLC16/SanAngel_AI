"""Admin-only minimal conversation and unresolved FAQ review routes."""

import asyncio
from datetime import date
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, Response

from backend.app.api.admin_authorization import require_admin_csrf, require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.config import get_admin_auth_settings, get_conversation_identity_settings
from backend.app.db.session import get_database_session_factory
from backend.app.schemas.admin_review import (
    ConversationDetail,
    ConversationPage,
    ResolveFAQRequest,
    ResolveFAQResult,
    UnresolvedItem,
    UnresolvedPage,
)
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.admin_review_service import AdminReviewService

router = APIRouter(prefix="/api/v1/admin/review", tags=["admin-review"])


def get_admin_review_service() -> AdminReviewService:
    return AdminReviewService(
        get_database_session_factory(),
        admin_settings=get_admin_auth_settings(),
        identity_settings=get_conversation_identity_settings(),
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
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0, le=5000)] = 0,
) -> ConversationPage:
    result = await asyncio.to_thread(
        service.list_conversations,
        principal,
        updated_from=updated_from,
        updated_to=updated_to,
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
