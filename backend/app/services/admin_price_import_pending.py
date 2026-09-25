"""Short-lived, session-bound review state for the admin price import UI."""

import hmac
from dataclasses import dataclass, field
from hashlib import sha256
from threading import Lock
from time import monotonic
from uuid import uuid4

from backend.app.services.price_import_transaction import PreparedPriceImport

PREVIEW_TTL_SECONDS = 10 * 60
MAX_PENDING_PREVIEWS = 16


@dataclass(frozen=True, slots=True)
class PendingPriceImport:
    content: bytes = field(repr=False)
    prepared: PreparedPriceImport = field(repr=False)
    session_digest: bytes = field(repr=False)
    user_id: int
    branch_id: int
    expires_at: float


class AdminPriceImportPendingStore:
    """One-process MVP store; previews expire and are consumed exactly once."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._entries: dict[str, PendingPriceImport] = {}

    def put(
        self,
        content: bytes,
        prepared: PreparedPriceImport,
        *,
        csrf: str,
        user_id: int,
        branch_id: int,
    ) -> str | None:
        now = monotonic()
        with self._lock:
            self._purge(now)
            if len(self._entries) >= MAX_PENDING_PREVIEWS:
                return None
            preview_id = uuid4().hex
            self._entries[preview_id] = PendingPriceImport(
                content=content,
                prepared=prepared,
                session_digest=sha256(csrf.encode("ascii")).digest(),
                user_id=user_id,
                branch_id=branch_id,
                expires_at=now + PREVIEW_TTL_SECONDS,
            )
            return preview_id

    def take(
        self, preview_id: str, *, csrf: str, user_id: int, branch_id: int
    ) -> PendingPriceImport | None:
        with self._lock:
            self._purge(monotonic())
            entry = self._entries.get(preview_id)
            if entry is None or entry.user_id != user_id or entry.branch_id != branch_id:
                return None
            if not hmac.compare_digest(entry.session_digest, sha256(csrf.encode("ascii")).digest()):
                return None
            return self._entries.pop(preview_id)

    def _purge(self, now: float) -> None:
        for preview_id, entry in tuple(self._entries.items()):
            if entry.expires_at <= now:
                del self._entries[preview_id]
