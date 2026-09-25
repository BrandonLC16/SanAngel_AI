"""Minimal admin review responses; never serialize phone, text, or HMAC keys."""

from datetime import datetime
from typing import Literal

from pydantic import UUID4, BaseModel, ConfigDict, Field, field_validator

from backend.app.core.conversation_mode import ConversationMode
from backend.app.schemas.admin_commercial import FAQWrite


class _ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ConversationItem(_ReviewModel):
    id: int
    channel: Literal["whatsapp"]
    created_at: datetime
    updated_at: datetime
    mode: ConversationMode
    assigned_to_me: bool


class ConversationPage(_ReviewModel):
    items: list[ConversationItem]
    has_more: bool


class MessageMetadata(_ReviewModel):
    direction: Literal["inbound", "outbound"]
    occurred_at: datetime


class ConversationDetail(ConversationItem):
    message_count: int
    recent_messages: list[MessageMetadata]
    manual_send_blocked: bool
    latest_manual_send: "ManualSendSummary | None"


class ConversationModeResult(_ReviewModel):
    mode: ConversationMode
    assigned_to_me: bool


class ManualSendSummary(_ReviewModel):
    receipt_id: int
    status: Literal["pending", "accepted", "uncertain"]
    created_at: datetime


class ManualReplyRequest(_ReviewModel):
    request_id: UUID4
    text: str = Field(min_length=1, max_length=2000)
    confirmed: Literal[True]

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized or "\x00" in normalized:
            raise ValueError("invalid manual reply text")
        return normalized


class ManualReplyResult(_ReviewModel):
    receipt_id: int
    status: Literal["pending", "accepted", "uncertain"]


class UnresolvedItem(_ReviewModel):
    id: int
    reason: Literal["faq_unknown", "faq_ambiguous"]
    occurrences: int
    first_seen_at: datetime
    last_seen_at: datetime


class UnresolvedPage(_ReviewModel):
    items: list[UnresolvedItem]
    has_more: bool


class ResolveFAQRequest(FAQWrite):
    is_active: Literal[True] = True


class ResolveFAQResult(_ReviewModel):
    faq_id: int = Field(gt=0)
    unresolved_id: int = Field(gt=0)
