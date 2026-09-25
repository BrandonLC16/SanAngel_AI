"""Minimal admin review responses; never serialize phone, text, or HMAC keys."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.admin_commercial import FAQWrite


class _ReviewModel(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)


class ConversationItem(_ReviewModel):
    id: int
    channel: Literal["whatsapp"]
    created_at: datetime
    updated_at: datetime


class ConversationPage(_ReviewModel):
    items: list[ConversationItem]
    has_more: bool


class MessageMetadata(_ReviewModel):
    direction: Literal["inbound", "outbound"]
    occurred_at: datetime


class ConversationDetail(ConversationItem):
    message_count: int
    recent_messages: list[MessageMetadata]


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
