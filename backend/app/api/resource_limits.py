"""Small, process-local HTTP admission and body budgets."""

import asyncio
from collections import OrderedDict
from collections.abc import Awaitable, Callable
from math import ceil, isfinite
from threading import Lock
from time import monotonic

from fastapi import Request, Response
from starlette.requests import ClientDisconnect

from backend.app.api.errors import create_error_response
from backend.app.core.config import HttpSettings

MAX_WEBHOOK_BODY_BYTES = 1024 * 1024
MAX_ADMIN_JSON_BYTES = 64 * 1024
MAX_INTERNAL_CHAT_BYTES = 16 * 1024
MAX_RATE_KEYS = 4096


class BodyTooLargeError(Exception):
    pass


class InvalidBodyLengthError(Exception):
    pass


class TokenBucket:
    """Bound memory while admitting bursts and replenishing at a fixed rate."""

    def __init__(
        self,
        *,
        rate_per_second: float,
        capacity: int,
        clock: Callable[[], float] = monotonic,
        max_keys: int = MAX_RATE_KEYS,
    ) -> None:
        if not isfinite(rate_per_second) or rate_per_second <= 0 or capacity < 1 or max_keys < 1:
            raise ValueError("invalid rate limit configuration")
        self._rate = rate_per_second
        self._capacity = capacity
        self._clock = clock
        self._max_keys = max_keys
        self._entries: OrderedDict[str, tuple[float, float]] = OrderedDict()
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        now = self._clock()
        with self._lock:
            previous = self._entries.pop(key, None)
            if previous is None:
                tokens = float(self._capacity)
                if len(self._entries) >= self._max_keys:
                    self._entries.popitem(last=False)
            else:
                tokens = min(
                    self._capacity,
                    previous[0] + max(0.0, now - previous[1]) * self._rate,
                )
            allowed = tokens >= 1
            self._entries[key] = (tokens - 1 if allowed else tokens, now)
            return allowed


class ResourceLimits:
    def __init__(self, settings: HttpSettings) -> None:
        self.admin = TokenBucket(
            rate_per_second=settings.admin_requests_per_minute / 60,
            capacity=settings.admin_requests_per_minute,
        )
        self.internal = TokenBucket(
            rate_per_second=settings.internal_requests_per_minute / 60,
            capacity=settings.internal_requests_per_minute,
        )
        self.webhook = TokenBucket(
            rate_per_second=settings.webhook_requests_per_second,
            capacity=2 * settings.webhook_requests_per_second,
            max_keys=1,
        )
        self.body_timeout_seconds = settings.http_body_read_timeout_seconds
        self.admin_retry_after = max(1, ceil(60 / settings.admin_requests_per_minute))
        self.internal_retry_after = max(1, ceil(60 / settings.internal_requests_per_minute))


def _declared_length(request: Request) -> int | None:
    values = request.headers.getlist("content-length")
    if not values:
        return None
    if len(values) != 1 or len(values[0]) > 20 or not values[0].isascii():
        raise InvalidBodyLengthError()
    if not values[0].isdigit():
        raise InvalidBodyLengthError()
    return int(values[0])


async def read_limited_body(request: Request, *, maximum: int, timeout: float) -> bytes:
    """Read at most maximum bytes, including requests without Content-Length."""

    declared = _declared_length(request)
    if declared is not None and declared > maximum:
        raise BodyTooLargeError()
    chunks: list[bytes] = []
    size = 0
    try:
        async with asyncio.timeout(timeout):
            async for chunk in request.stream():
                size += len(chunk)
                if size > maximum:
                    raise BodyTooLargeError()
                chunks.append(chunk)
    except ClientDisconnect:
        raise TimeoutError("request body disconnected") from None
    body = b"".join(chunks)
    request._body = body  # Starlette replays this cached body to the route.
    return body


def _rejected(
    request: Request, *, status: int, code: str, message: str, retry_after: int = 1
) -> Response:
    request.state.error_category = code
    response = create_error_response(
        request, status_code=status, error_code=code, public_message=message
    )
    if status == 429:
        response.headers["Retry-After"] = str(retry_after)
    return response


async def resource_limit_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Limit admin and internal traffic before route parsing; webhook checks after auth."""

    path = request.url.path
    limits: ResourceLimits = request.app.state.resource_limits
    if path.startswith("/api/v1/admin/"):
        bucket = limits.admin
        retry_after = limits.admin_retry_after
        maximum = MAX_ADMIN_JSON_BYTES
    elif path == "/api/v1/chat":
        bucket = limits.internal
        retry_after = limits.internal_retry_after
        maximum = MAX_INTERNAL_CHAT_BYTES
    else:
        return await call_next(request)

    peer = request.client.host if request.client is not None else "unknown"
    if not bucket.allow(peer):
        return _rejected(
            request,
            status=429,
            code="request_rate_limited",
            message="Demasiadas solicitudes. Inténtalo más tarde.",
            retry_after=retry_after,
        )
    # Excel preview already streams a 2 MiB cap after session and CSRF checks.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and path != (
        "/api/v1/admin/price-import/preview"
    ):
        try:
            await read_limited_body(request, maximum=maximum, timeout=limits.body_timeout_seconds)
        except BodyTooLargeError:
            return _rejected(
                request,
                status=413,
                code="request_body_too_large",
                message="El cuerpo de la solicitud supera el límite permitido.",
            )
        except InvalidBodyLengthError:
            return _rejected(
                request,
                status=400,
                code="invalid_content_length",
                message="La solicitud no es válida.",
            )
        except TimeoutError:
            return _rejected(
                request,
                status=408,
                code="request_body_timeout",
                message="La lectura de la solicitud tardó demasiado.",
            )
    return await call_next(request)
