import asyncio
from typing import Protocol

from backend.app.core.exceptions import IdempotencyStoreError

DEFAULT_MAX_IDEMPOTENCY_ENTRIES = 10_000


class IdempotencyStore(Protocol):
    """Coordinate exclusive processing of provider message identifiers."""

    async def claim(self, message_id: str) -> bool: ...

    async def mark_processed(self, message_id: str) -> None: ...

    async def release(self, message_id: str) -> None: ...


class InMemoryIdempotencyStore:
    """Bounded, process-local MVP store; never use as production persistence."""

    def __init__(self, max_entries: int = DEFAULT_MAX_IDEMPOTENCY_ENTRIES) -> None:
        if not isinstance(max_entries, int) or isinstance(max_entries, bool) or max_entries <= 0:
            raise ValueError("max_entries must be a positive integer")
        self._max_entries = max_entries
        self._entries: dict[str, bool] = {}
        self._lock = asyncio.Lock()

    async def claim(self, message_id: str) -> bool:
        """Atomically reserve an unseen ID, rejecting duplicates already in flight or done."""

        self._validate_message_id(message_id)
        async with self._lock:
            if message_id in self._entries:
                return False

            if len(self._entries) >= self._max_entries:
                self._evict_oldest_processed()

            self._entries[message_id] = False
            return True

    async def mark_processed(self, message_id: str) -> None:
        """Retain a successfully processed ID until bounded eviction removes it."""

        self._validate_message_id(message_id)
        async with self._lock:
            if message_id not in self._entries:
                raise IdempotencyStoreError("cannot complete an unclaimed message id")
            self._entries[message_id] = True

    async def release(self, message_id: str) -> None:
        """Allow a later retry when processing did not complete successfully."""

        self._validate_message_id(message_id)
        async with self._lock:
            self._entries.pop(message_id, None)

    def _evict_oldest_processed(self) -> None:
        for candidate, is_processed in self._entries.items():
            if is_processed:
                del self._entries[candidate]
                return
        raise IdempotencyStoreError("all in-memory idempotency entries are in progress")

    @staticmethod
    def _validate_message_id(message_id: str) -> None:
        if not isinstance(message_id, str) or not message_id:
            raise ValueError("message_id must be a non-empty string")
