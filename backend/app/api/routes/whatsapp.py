import hmac
from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status

from backend.app.api.dependencies import get_inbound_queue_factory
from backend.app.api.resource_limits import (
    MAX_WEBHOOK_BODY_BYTES,
    BodyTooLargeError,
    InvalidBodyLengthError,
    ResourceLimits,
    read_limited_body,
)
from backend.app.core.config import Settings, get_settings
from backend.app.core.exceptions import ApplicationError
from backend.app.services.whatsapp_inbound_queue import PersistentInboundQueue
from backend.app.services.whatsapp_webhook_service import WhatsAppWebhookService

router = APIRouter(prefix="/api/v1/whatsapp", tags=["whatsapp"])

_AUTHORIZATION_HEADER = "Authorization"
_MAX_AUTHORIZATION_BYTES = 2048


def _get_single_header_value(request: Request, name: str) -> str | None:
    values = request.headers.getlist(name)
    if len(values) != 1:
        return None
    return values[0]


def _has_valid_green_api_authorization(
    authorization_header: str | None,
    webhook_token: str,
) -> bool:
    if authorization_header is None:
        return False

    received = authorization_header.encode("utf-8")
    expected = f"Bearer {webhook_token}".encode()
    return len(received) <= _MAX_AUTHORIZATION_BYTES and hmac.compare_digest(received, expected)


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Recibir webhook autenticado de WhatsApp mediante GREEN-API",
)
async def receive_whatsapp_webhook(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)],
    queue_factory: Annotated[
        Callable[[Settings], PersistentInboundQueue],
        Depends(get_inbound_queue_factory),
    ],
) -> Response:
    """Authenticate GREEN-API before parsing an incoming webhook body."""

    configured_webhook_token = settings.green_api_webhook_token
    configured_instance_id = settings.green_api_instance_id
    if configured_webhook_token is None or configured_instance_id is None:
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    authorization_header = _get_single_header_value(request, _AUTHORIZATION_HEADER)
    if not _has_valid_green_api_authorization(
        authorization_header,
        configured_webhook_token.get_secret_value(),
    ):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    limits: ResourceLimits = request.app.state.resource_limits
    if not limits.webhook.allow("configured-instance"):
        request.state.error_category = "webhook_rate_limited"
        return Response(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": "1"},
        )
    try:
        raw_body = await read_limited_body(
            request,
            maximum=MAX_WEBHOOK_BODY_BYTES,
            timeout=limits.body_timeout_seconds,
        )
    except (BodyTooLargeError, InvalidBodyLengthError):
        # A non-200 response would retry the same unusable notification ahead of the queue.
        request.state.error_category = "webhook_body_rejected"
        return Response(status_code=status.HTTP_200_OK)
    except TimeoutError:
        request.state.error_category = "webhook_body_timeout"
        return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)
    webhook_service = WhatsAppWebhookService(
        max_text_chars=settings.chat_max_message_chars,
        expected_instance_id=configured_instance_id,
    )
    inbound_messages = webhook_service.parse_messages(raw_body)
    if inbound_messages:
        try:
            await queue_factory(settings).enqueue(inbound_messages)
        except ApplicationError:
            request.state.error_category = "service_unavailable"
            return Response(status_code=status.HTTP_503_SERVICE_UNAVAILABLE)

    return Response(status_code=status.HTTP_200_OK)
