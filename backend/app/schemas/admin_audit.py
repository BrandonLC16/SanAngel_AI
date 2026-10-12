"""Allowlisted audit view without credentials or arbitrary business text."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    source: Literal["commercial", "role", "conversation"]
    actor_user_id: int | None
    action: Literal[
        "create",
        "update",
        "deactivate",
        "delete",
        "take",
        "release",
        "help_requested",
        "send_pending",
        "send_accepted",
        "send_uncertain",
    ]
    entity: Literal["branch", "product", "price", "faq", "admin_user", "conversation"]
    entity_id: int
    occurred_at: datetime
    product_id: int | None = None
    unit: str | None = None
    before: dict[str, str] | None = None
    after: dict[str, str] | None = None


class AuditPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[AuditEvent]
    has_more: bool
