import logging
import re
from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response

from backend.app.api.errors import REQUEST_ID_HEADER, create_error_response
from backend.app.core.logging import http_logger

RequestHandler = Callable[[Request], Awaitable[Response]]
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def resolve_request_id(candidate: str | None) -> str:
    """Accept a bounded safe request ID or generate a new opaque identifier."""

    if candidate is not None and REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate
    return uuid4().hex


def get_route_template(request: Request) -> str:
    route = request.scope.get("route")
    route_template = getattr(route, "path", None)
    return route_template if isinstance(route_template, str) else "<unmatched>"


def log_request(
    request: Request,
    *,
    status_code: int,
    duration_ms: float,
    error_category: str,
) -> None:
    if status_code >= 500:
        log_level = logging.ERROR
    elif status_code >= 400:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    http_logger.log(
        log_level,
        (
            "request_complete request_id=%s method=%s endpoint=%s "
            "status_code=%d duration_ms=%.2f error_category=%s"
        ),
        request.state.request_id,
        request.method,
        get_route_template(request),
        status_code,
        duration_ms,
        error_category,
    )


async def request_context_middleware(request: Request, call_next: RequestHandler) -> Response:
    """Propagate a safe request ID and emit metadata-only request logs."""

    request.state.request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
    started_at = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        request.state.error_category = "unhandled_exception"
        response = create_error_response(
            request,
            status_code=500,
            error_code="internal_error",
            public_message="Ocurrió un error interno.",
        )

    response.headers[REQUEST_ID_HEADER] = request.state.request_id
    log_request(
        request,
        status_code=response.status_code,
        duration_ms=(perf_counter() - started_at) * 1000,
        error_category=getattr(request.state, "error_category", "none"),
    )
    return response


async def safe_exception_middleware(request: Request, call_next: RequestHandler) -> Response:
    """Convert unexpected endpoint errors before CORS processes the response."""

    try:
        return await call_next(request)
    except Exception:
        request.state.error_category = "unhandled_exception"
        return create_error_response(
            request,
            status_code=500,
            error_code="internal_error",
            public_message="Ocurrió un error interno.",
        )
