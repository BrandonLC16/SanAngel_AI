from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_WEBHOOK_ITEMS = 1000
MAX_WHATSAPP_TEXT_CHARS = 10_000


class WhatsAppProviderModel(BaseModel):
    """Tolerant provider model: unknown Meta fields are ignored by design."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class WhatsAppTextPayload(WhatsAppProviderModel):
    body: str = Field(max_length=MAX_WHATSAPP_TEXT_CHARS)


class WhatsAppMessagePayload(WhatsAppProviderModel):
    external_message_id: str = Field(alias="id", min_length=1, max_length=512)
    sender_id: str = Field(alias="from", pattern=r"^[0-9]{1,64}$")
    message_type: str = Field(alias="type", min_length=1, max_length=64)
    timestamp: str | None = Field(default=None, pattern=r"^[0-9]{1,20}$")
    text: WhatsAppTextPayload | None = None


class WhatsAppWebhookValue(WhatsAppProviderModel):
    messaging_product: str | None = Field(default=None, max_length=64)
    messages: tuple[WhatsAppMessagePayload, ...] = Field(
        default=(),
        max_length=MAX_WEBHOOK_ITEMS,
    )


class WhatsAppWebhookChange(WhatsAppProviderModel):
    field: str | None = Field(default=None, max_length=64)
    value: WhatsAppWebhookValue | None = None


class WhatsAppWebhookEntry(WhatsAppProviderModel):
    changes: tuple[WhatsAppWebhookChange, ...] = Field(
        default=(),
        max_length=MAX_WEBHOOK_ITEMS,
    )


class WhatsAppWebhookPayload(WhatsAppProviderModel):
    object: str | None = Field(default=None, max_length=64)
    entry: tuple[WhatsAppWebhookEntry, ...] = Field(
        default=(),
        max_length=MAX_WEBHOOK_ITEMS,
    )


class InboundMessage(BaseModel):
    """Provider-independent message accepted by the internal application boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Literal["whatsapp"] = "whatsapp"
    external_message_id: str = Field(min_length=1, max_length=512)
    sender_id: str = Field(pattern=r"^[0-9]{1,64}$")
    message_type: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=MAX_WHATSAPP_TEXT_CHARS)
    timestamp: int | None = Field(default=None, ge=0)


class WhatsAppSentMessage(WhatsAppProviderModel):
    id: str = Field(min_length=1, max_length=512)


class WhatsAppSendResponse(WhatsAppProviderModel):
    messages: tuple[WhatsAppSentMessage, ...] = Field(min_length=1, max_length=1000)
