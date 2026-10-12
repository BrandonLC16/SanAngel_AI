"""TLS admission and response headers at the HTTP boundary."""

from collections.abc import Awaitable, Callable
from ipaddress import ip_address

from fastapi import Request, Response

from backend.app.api.errors import create_error_response
from backend.app.core.config import HttpSettings


def _trusted_https(request: Request, settings: HttpSettings) -> bool:
    if request.scope["scheme"] == "https":
        return True
    if request.client is None:
        return False
    try:
        peer = str(ip_address(request.client.host))
    except ValueError:
        return False
    if peer not in settings.trusted_proxy_ips:
        return False
    # A single, exact value is required. Never use X-Forwarded-For/Host or Forwarded.
    if request.headers.getlist("x-forwarded-proto") != ["https"]:
        return False
    request.scope["scheme"] = "https"
    return True


async def transport_security_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    settings: HttpSettings = request.app.state.http_settings
    secure = _trusted_https(request, settings)
    request.state.secure_transport = secure
    if settings.app_env == "production" and not secure:
        request.state.error_category = "https_required"
        return create_error_response(
            request,
            status_code=403,
            error_code="https_required",
            public_message="Se requiere HTTPS.",
        )
    return await call_next(request)


def apply_security_headers(request: Request, response: Response) -> None:
    """Run outside all other middleware so even fallback errors receive headers."""
    settings: HttpSettings = request.app.state.http_settings
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if getattr(request.state, "secure_transport", False) and settings.app_env == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    if request.url.path.startswith("/api/v1/admin/"):
        response.headers["Cache-Control"] = "no-store"
