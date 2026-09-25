"""Encrypt the WhatsApp destination kept for an assigned human reply."""

import base64
import hashlib
import hmac
import re

from cryptography.fernet import Fernet, InvalidToken

from backend.app.core.config import ConversationIdentitySettings
from backend.app.core.exceptions import (
    ConversationRecipientUnavailableError,
    InvalidRequestError,
    ServiceUnavailableError,
)
from backend.app.db.models.conversation import Conversation
from backend.app.schemas.whatsapp import GREEN_API_CHAT_ID_PATTERN

_CHAT_ID = re.compile(GREEN_API_CHAT_ID_PATTERN)


class ConversationRecipientCipher:
    """Use a domain-separated subkey; never serialize plaintext to admin responses."""

    def __init__(self, settings: ConversationIdentitySettings) -> None:
        key = settings.conversation_identity_key.get_secret_value().encode("ascii")
        subkey = hmac.new(key, b"conversation-recipient:v1", hashlib.sha256).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(subkey))
        self._identity_key = key
        self._branch_code = settings.assistant_branch_code

    def encrypt(self, chat_id: str) -> str:
        if not isinstance(chat_id, str) or _CHAT_ID.fullmatch(chat_id) is None:
            raise InvalidRequestError("invalid WhatsApp recipient")
        return self._fernet.encrypt(f"{self._branch_code}\n{chat_id}".encode()).decode("ascii")

    def decrypt(self, conversation: Conversation) -> str:
        if conversation.recipient_ciphertext is None:
            raise ConversationRecipientUnavailableError()
        try:
            plaintext = self._fernet.decrypt(conversation.recipient_ciphertext.encode("ascii"))
            branch_code, chat_id = plaintext.decode("utf-8").split("\n", 1)
        except (InvalidToken, UnicodeError, ValueError):
            raise ServiceUnavailableError("conversation recipient cannot be decrypted") from None
        identity = hmac.new(
            self._identity_key, f"whatsapp:{chat_id}".encode(), hashlib.sha256
        ).hexdigest()
        if (
            branch_code != self._branch_code
            or _CHAT_ID.fullmatch(chat_id) is None
            or not hmac.compare_digest(identity, conversation.external_user_key)
        ):
            raise ServiceUnavailableError("conversation recipient does not match identity")
        return chat_id
