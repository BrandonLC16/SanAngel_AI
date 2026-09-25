"""Authenticated Excel price import preview and explicit confirmation."""

import asyncio
import re
from typing import Annotated, Literal
from urllib.parse import unquote_to_bytes

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict

from backend.app.api.admin_authorization import require_admin_csrf, require_permission
from backend.app.core.admin_roles import AdminPermission
from backend.app.core.config import get_admin_auth_settings
from backend.app.core.exceptions import ApplicationError, InvalidRequestError
from backend.app.db.session import get_database_session_factory
from backend.app.repositories.price_import_audit_repository import ImportActor
from backend.app.services.admin_auth_service import AdminSessionInfo
from backend.app.services.admin_price_import_pending import AdminPriceImportPendingStore
from backend.app.services.branch_scope import BranchScope
from backend.app.services.price_import_parser import MAX_PRICE_IMPORT_BYTES
from backend.app.services.price_import_transaction import (
    PriceImportAuditError,
    PriceImportConfirmationError,
    PriceImportStalePreviewError,
    PriceImportTransactionService,
    PriceImportValidationError,
    PriceImportWriteError,
)

router = APIRouter(prefix="/api/v1/admin/price-import", tags=["admin-price-import"])
PREVIEW_ID = re.compile(r"[0-9a-f]{32}")


class PriceImportTooLarge(ApplicationError):
    error_code = "price_import_too_large"
    public_message = "El archivo supera el límite de 2 MiB."
    status_code = 413


class PriceImportReviewUnavailable(ApplicationError):
    error_code = "price_import_review_unavailable"
    public_message = "La vista previa venció o ya se utilizó. Carga el archivo de nuevo."
    status_code = 409


class PriceImportUnavailable(ApplicationError):
    error_code = "price_import_unavailable"
    public_message = "No se pudo completar la importación. Inténtalo más tarde."
    status_code = 503


class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preview_id: str
    confirmed: Literal[True]


def _service() -> PriceImportTransactionService:
    return PriceImportTransactionService(
        get_database_session_factory(),
        branch_scope=BranchScope.from_settings(get_admin_auth_settings()),
    )


async def _bounded_workbook(request: Request) -> bytes:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ):
        raise InvalidRequestError()
    declared = request.headers.get("content-length")
    if declared is not None:
        try:
            if int(declared) > MAX_PRICE_IMPORT_BYTES:
                raise PriceImportTooLarge()
        except ValueError:
            raise InvalidRequestError() from None
    chunks: list[bytes] = []
    size = 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > MAX_PRICE_IMPORT_BYTES:
            raise PriceImportTooLarge()
        chunks.append(chunk)
    return b"".join(chunks)


def _workbook_filename(request: Request) -> str:
    encoded = request.headers.get("x-file-name", "")
    if not encoded or len(encoded) > 512 or not encoded.isascii():
        raise InvalidRequestError()
    try:
        filename = unquote_to_bytes(encoded).decode("utf-8", errors="strict")
    except UnicodeError:
        raise InvalidRequestError() from None
    if len(filename) > 255 or not filename.isprintable():
        raise InvalidRequestError()
    return filename


@router.post("/preview")
async def preview_price_import(
    request: Request,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    csrf: Annotated[str, Depends(require_admin_csrf)],
    service: Annotated[PriceImportTransactionService, Depends(_service)],
) -> dict[str, object]:
    filename = _workbook_filename(request)
    content = await _bounded_workbook(request)
    prepared = await asyncio.to_thread(service.prepare, content, filename=filename)
    result = prepared.preview.to_review_data()
    response.headers["Cache-Control"] = "no-store"
    preview_id = None
    if prepared.preview.is_valid:
        store: AdminPriceImportPendingStore = request.app.state.price_import_pending
        preview_id = store.put(
            content, prepared, csrf=csrf, user_id=principal.user_id, branch_id=principal.branch_id
        )
        if preview_id is None:
            raise PriceImportUnavailable()
    return {"branch_code": prepared.branch_code, "preview_id": preview_id, **result}


@router.post("/confirm")
async def confirm_price_import(
    payload: ConfirmRequest,
    request: Request,
    response: Response,
    principal: Annotated[
        AdminSessionInfo, Depends(require_permission(AdminPermission.COMMERCIAL_WRITE))
    ],
    csrf: Annotated[str, Depends(require_admin_csrf)],
    service: Annotated[PriceImportTransactionService, Depends(_service)],
) -> dict[str, object]:
    if PREVIEW_ID.fullmatch(payload.preview_id) is None:
        raise InvalidRequestError()
    store: AdminPriceImportPendingStore = request.app.state.price_import_pending
    pending = store.take(
        payload.preview_id, csrf=csrf, user_id=principal.user_id, branch_id=principal.branch_id
    )
    if pending is None:
        raise PriceImportReviewUnavailable()
    try:
        receipt = await asyncio.to_thread(
            service.confirm,
            pending.content,
            filename=pending.prepared.filename,
            prepared=pending.prepared,
            confirmed=True,
            actor=ImportActor(f"admin-{principal.user_id}"),
        )
    except (PriceImportConfirmationError, PriceImportValidationError, PriceImportStalePreviewError):
        raise PriceImportReviewUnavailable() from None
    except (PriceImportWriteError, PriceImportAuditError):
        raise PriceImportUnavailable() from None
    response.headers["Cache-Control"] = "no-store"
    return {
        "audit_id": receipt.audit_id,
        "attempt_id": receipt.attempt_id,
        "branch_code": receipt.branch_code,
        "created": receipt.created,
        "updated": receipt.updated,
        "unchanged": receipt.unchanged,
    }
