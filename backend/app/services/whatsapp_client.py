import logging
import re
from collections.abc import Mapping
from typing import Protocol, Self

import httpx
from pydantic import ValidationError

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    WhatsAppClientConfigurationError,
    WhatsAppClientInputError,
    WhatsAppProviderConnectionError,
    WhatsAppProviderRateLimitError,
    WhatsAppProviderResponseError,
    WhatsAppProviderStatusError,
    WhatsAppProviderTimeoutError,
)
from backend.app.schemas.whatsapp import GREEN_API_CHAT_ID_PATTERN, WhatsAppSendResponse

MAX_OUTBOUND_TEXT_CHARS = 20_000
_RECIPIENT_PATTERN = re.compile(GREEN_API_CHAT_ID_PATTERN)


def _disable_http_url_logging() -> None:
    """Prevent dependencies from logging GREEN-API URLs that contain the instance token."""

    for logger_name in ("httpx", "httpcore"):
        provider_logger = logging.getLogger(logger_name)
        if provider_logger.level < logging.WARNING:
            provider_logger.setLevel(logging.WARNING)


def _green_api_error_code(response: httpx.Response) -> int | None:
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    code = payload.get("code")
    return code if isinstance(code, int) and not isinstance(code, bool) else None


class AsyncHTTPClient(Protocol):
    async def post(
        self,
        url: str,
        *,
        headers: Mapping[str, str],
        json: object,
        timeout: float,
        follow_redirects: bool,
    ) -> httpx.Response: ...


class WhatsAppClient:
    """Send WhatsApp text messages through GREEN-API without content logging."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: AsyncHTTPClient | None = None,
    ) -> None:
        _disable_http_url_logging()
        instance_id = settings.green_api_instance_id
        token_instance = settings.green_api_token_instance
        if instance_id is None or token_instance is None:
            raise WhatsAppClientConfigurationError("WhatsApp client configuration is incomplete")

        self._endpoint = (
            f"{settings.green_api_api_url}/waInstance{instance_id}/sendMessage/"
            f"{token_instance.get_secret_value()}"
        )
        self._timeout = settings.whatsapp_request_timeout_seconds

        if http_client is None:
            owned_client = httpx.AsyncClient(follow_redirects=False)
            self._http_client: AsyncHTTPClient = owned_client
            self._owned_http_client: httpx.AsyncClient | None = owned_client
        else:
            self._http_client = http_client
            self._owned_http_client = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owned_http_client is not None:
            await self._owned_http_client.aclose()
            self._owned_http_client = None

    async def send_text(
        self,
        recipient: str,
        text: str,
        *,
        preview_url: bool = False,
    ) -> str:
        if _RECIPIENT_PATTERN.fullmatch(recipient) is None:
            raise WhatsAppClientInputError("WhatsApp recipient has an invalid format")

        if len(text) > MAX_OUTBOUND_TEXT_CHARS:
            raise WhatsAppClientInputError("WhatsApp text exceeds the supported limit")
        normalized_text = text.strip()
        if not normalized_text:
            raise WhatsAppClientInputError("WhatsApp text must not be blank")

        headers = {"Content-Type": "application/json"}
        payload = {
            "chatId": recipient,
            "message": normalized_text,
            "linkPreview": preview_url,
        }

        try:
            response = await self._http_client.post(
                self._endpoint,
                headers=headers,
                json=payload,
                timeout=self._timeout,
                follow_redirects=False,
            )
        except httpx.TimeoutException:
            raise WhatsAppProviderTimeoutError("GREEN-API timeout") from None
        except httpx.RequestError:
            raise WhatsAppProviderConnectionError("GREEN-API connection failure") from None

        if response.status_code == 429:
            raise WhatsAppProviderRateLimitError("GREEN-API rate limit")
        if not 200 <= response.status_code < 300:
            provider_code = _green_api_error_code(response) or response.status_code
            raise WhatsAppProviderStatusError(
                "GREEN-API HTTP failure",
                provider_code=provider_code,
            )

        provider_code = _green_api_error_code(response)
        if provider_code is not None:
            raise WhatsAppProviderStatusError(
                "GREEN-API returned an error response",
                provider_code=provider_code,
            )

        try:
            parsed_response = WhatsAppSendResponse.model_validate_json(response.content)
        except ValidationError:
            raise WhatsAppProviderResponseError("GREEN-API returned an invalid response") from None

        return parsed_response.id_message
