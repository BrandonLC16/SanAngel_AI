"""Backend-owned responder modes for one WhatsApp conversation."""

from enum import StrEnum


class ConversationMode(StrEnum):
    AI = "AI"
    HUMAN = "HUMAN"
