from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

MAX_WHATSAPP_TEXT_CHARS = 10_000
GREEN_API_CHAT_ID_PATTERN = r"^(?:[1-9][0-9]{5,19}@c\.us|[1-9][0-9]{5,24}(?:-[0-9]{1,20})?@g\.us)$"


class WhatsAppProviderModel(BaseModel):
    """Tolerant provider model: unknown GREEN-API fields are ignored by design."""

    model_config = ConfigDict(extra="ignore", frozen=True)


class GreenAPIInstanceData(WhatsAppProviderModel):
    instance_id: int = Field(alias="idInstance", ge=1, le=99_999_999_999_999_999_999)
    instance_type: str = Field(alias="typeInstance", min_length=1, max_length=64)


class GreenAPISenderData(WhatsAppProviderModel):
    chat_id: str = Field(alias="chatId", max_length=128)


class GreenAPITextMessageData(WhatsAppProviderModel):
    text: str = Field(alias="textMessage", max_length=MAX_WHATSAPP_TEXT_CHARS)


class GreenAPIExtendedTextMessageData(WhatsAppProviderModel):
    text: str = Field(max_length=MAX_WHATSAPP_TEXT_CHARS)


class GreenAPIMessageData(WhatsAppProviderModel):
    message_type: str = Field(alias="typeMessage", min_length=1, max_length=64)
    text_message_data: GreenAPITextMessageData | None = Field(
        default=None,
        alias="textMessageData",
    )
    extended_text_message_data: GreenAPIExtendedTextMessageData | None = Field(
        default=None,
        alias="extendedTextMessageData",
    )


class GreenAPIWebhookPayload(WhatsAppProviderModel):
    webhook_type: str = Field(alias="typeWebhook", min_length=1, max_length=64)
    instance_data: GreenAPIInstanceData = Field(alias="instanceData")
    timestamp: int = Field(ge=0)
    external_message_id: str = Field(alias="idMessage", min_length=1, max_length=512)
    sender_data: GreenAPISenderData = Field(alias="senderData")
    message_data: GreenAPIMessageData = Field(alias="messageData")


class InboundMessage(BaseModel):
    """Provider-independent message accepted by the internal application boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: Literal["whatsapp"] = "whatsapp"
    external_message_id: str = Field(min_length=1, max_length=512)
    sender_id: str = Field(pattern=GREEN_API_CHAT_ID_PATTERN)
    message_type: Literal["text"] = "text"
    text: str = Field(min_length=1, max_length=MAX_WHATSAPP_TEXT_CHARS)
    timestamp: int | None = Field(default=None, ge=0)


class WhatsAppSendResponse(WhatsAppProviderModel):
    id_message: str = Field(alias="idMessage", min_length=1, max_length=512)
