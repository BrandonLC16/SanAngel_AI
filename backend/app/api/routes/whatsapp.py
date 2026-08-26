import hashlib
import hmac
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.responses import PlainTextResponse

from backend.app.core.config import Settings, get_settings
from backend.app.services.whatsapp_webhook_service import WhatsAppWebhookService

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

_CHALLENGE_PATTERN = re.compile(r"[0-9]{1,20}")
_META_SIGNATURE_PATTERN = re.compile(r"sha256=([0-9a-f]{64})")
_MAX_VERIFY_TOKEN_BYTES = 1024
_META_SIGNATURE_HEADER = "X-Hub-Signature-256"


def _get_single_query_value(request: Request, name: str) -> str | None:
    values = request.query_params.getlist(name)
    if len(values) != 1:
        return None
    return values[0]


def _get_single_header_value(request: Request, name: str) -> str | None:
    values = request.headers.getlist(name)
    if len(values) != 1:
        return None
    return values[0]


def _has_valid_meta_signature(
    raw_body: bytes,
    signature_header: str | None,
    app_secret: bytes,
) -> bool:
    if signature_header is None:
        return False

    signature_match = _META_SIGNATURE_PATTERN.fullmatch(signature_header)
    if signature_match is None:
        return False

    expected_signature = hmac.new(app_secret, raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature_match.group(1), expected_signature)


@router.get(
    "/webhook",
    response_class=PlainTextResponse,
    summary="Verificar webhook de WhatsApp",
)
def verify_whatsapp_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """Complete Meta's GET verification without logging or reflecting the verify token."""

    configured_token = settings.whatsapp_verify_token
    if configured_token is None:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    mode = _get_single_query_value(request, "hub.mode")
    received_token = _get_single_query_value(request, "hub.verify_token")
    challenge = _get_single_query_value(request, "hub.challenge")

    expected_token_bytes = configured_token.get_secret_value().encode("utf-8")
    received_token_bytes = received_token.encode("utf-8") if received_token is not None else b""
    token_matches = len(received_token_bytes) <= _MAX_VERIFY_TOKEN_BYTES and hmac.compare_digest(
        received_token_bytes,
        expected_token_bytes,
    )
    challenge_is_valid = challenge is not None and _CHALLENGE_PATTERN.fullmatch(challenge)

    if mode != "subscribe" or not token_matches or not challenge_is_valid:
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    return PlainTextResponse(content=challenge)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Recibir webhook autenticado de WhatsApp",
)
async def receive_whatsapp_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
) -> Response:
    """Authenticate Meta's signature over the untouched body before any JSON processing."""

    configured_app_secret = settings.meta_app_secret
    if configured_app_secret is None:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    raw_body = await request.body()
    signature_header = _get_single_header_value(request, _META_SIGNATURE_HEADER)
    app_secret = configured_app_secret.get_secret_value().encode("utf-8")

    if not _has_valid_meta_signature(raw_body, signature_header, app_secret):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    webhook_service = WhatsAppWebhookService(max_text_chars=settings.chat_max_message_chars)
    webhook_service.parse_messages(raw_body)
    return Response(status_code=status.HTTP_200_OK)
