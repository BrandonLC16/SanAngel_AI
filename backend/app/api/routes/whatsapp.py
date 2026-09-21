import hmac
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Request, Response, status

from backend.app.api.dependencies import get_whatsapp_background_processor
from backend.app.core.config import Settings, get_settings
from backend.app.services.whatsapp_background_processor import WhatsAppBackgroundProcessor
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
    background_tasks: BackgroundTasks,
    settings: Annotated[Settings, Depends(get_settings)],
    background_processor: Annotated[
        WhatsAppBackgroundProcessor,
        Depends(get_whatsapp_background_processor),
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

    raw_body = await request.body()
    webhook_service = WhatsAppWebhookService(
        max_text_chars=settings.chat_max_message_chars,
        expected_instance_id=configured_instance_id,
    )
    inbound_messages = webhook_service.parse_messages(raw_body)
    if inbound_messages:
        background_tasks.add_task(
            background_processor.process_messages,
            inbound_messages,
            settings,
            request.state.request_id,
        )

    return Response(status_code=status.HTTP_200_OK)
