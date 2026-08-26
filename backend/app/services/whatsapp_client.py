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
from backend.app.schemas.whatsapp import WhatsAppSendResponse

GRAPH_API_BASE_URL = "https://graph.facebook.com"
MAX_OUTBOUND_TEXT_CHARS = 4096
_RECIPIENT_PATTERN = re.compile(r"\+?[1-9][0-9]{5,14}")


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
    """Send WhatsApp messages through a fixed Graph API boundary without content logging."""

    def __init__(
        self,
        settings: Settings,
        *,
        http_client: AsyncHTTPClient | None = None,
    ) -> None:
        access_token = settings.whatsapp_access_token
        phone_number_id = settings.whatsapp_phone_number_id
        if access_token is None or phone_number_id is None:
            raise WhatsAppClientConfigurationError("WhatsApp client configuration is incomplete")

        self._access_token = access_token
        self._endpoint = (
            f"{GRAPH_API_BASE_URL}/{settings.meta_graph_api_version}/{phone_number_id}/messages"
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

        headers = {
            "Authorization": f"Bearer {self._access_token.get_secret_value()}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": preview_url,
                "body": normalized_text,
            },
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
            raise WhatsAppProviderTimeoutError("Graph API timeout") from None
        except httpx.RequestError:
            raise WhatsAppProviderConnectionError("Graph API connection failure") from None

        if response.status_code == 429:
            raise WhatsAppProviderRateLimitError("Graph API rate limit")
        if not 200 <= response.status_code < 300:
            raise WhatsAppProviderStatusError("Graph API HTTP failure")

        try:
            parsed_response = WhatsAppSendResponse.model_validate_json(response.content)
        except ValidationError:
            raise WhatsAppProviderResponseError("Graph API returned an invalid response") from None

        return parsed_response.messages[0].id
