import asyncio

import pytest

from backend.app.core.exceptions import IdempotencyStoreError
from backend.app.services.idempotency_store import InMemoryIdempotencyStore


def test_claim_is_atomic_for_concurrent_attempts() -> None:
    store = InMemoryIdempotencyStore()

    async def claim_concurrently() -> list[bool]:
        return await asyncio.gather(
            store.claim("whatsapp:wamid.test-only-id"),
            store.claim("whatsapp:wamid.test-only-id"),
        )

    results = asyncio.run(claim_concurrently())

    assert sorted(results) == [False, True]


def test_processed_id_remains_a_duplicate() -> None:
    store = InMemoryIdempotencyStore()

    async def complete_and_retry() -> bool:
        assert await store.claim("whatsapp:wamid.test-only-id")
        await store.mark_processed("whatsapp:wamid.test-only-id")
        return await store.claim("whatsapp:wamid.test-only-id")

    assert asyncio.run(complete_and_retry()) is False


def test_release_allows_retry_after_failed_processing() -> None:
    store = InMemoryIdempotencyStore()

    async def release_and_retry() -> bool:
        assert await store.claim("whatsapp:wamid.test-only-id")
        await store.release("whatsapp:wamid.test-only-id")
        return await store.claim("whatsapp:wamid.test-only-id")

    assert asyncio.run(release_and_retry()) is True


def test_bounded_store_evicts_oldest_completed_id() -> None:
    store = InMemoryIdempotencyStore(max_entries=2)

    async def fill_and_evict() -> tuple[bool, bool, bool]:
        assert await store.claim("whatsapp:wamid.first")
        await store.mark_processed("whatsapp:wamid.first")
        assert await store.claim("whatsapp:wamid.second")
        await store.mark_processed("whatsapp:wamid.second")
        new_claim = await store.claim("whatsapp:wamid.third")
        retained_claim = await store.claim("whatsapp:wamid.second")
        evicted_claim = await store.claim("whatsapp:wamid.first")
        return new_claim, retained_claim, evicted_claim

    assert asyncio.run(fill_and_evict()) == (True, False, True)


def test_capacity_does_not_evict_messages_still_in_progress() -> None:
    store = InMemoryIdempotencyStore(max_entries=1)

    async def exceed_capacity() -> None:
        assert await store.claim("whatsapp:wamid.in-progress")
        await store.claim("whatsapp:wamid.new")

    with pytest.raises(IdempotencyStoreError):
        asyncio.run(exceed_capacity())


@pytest.mark.parametrize("max_entries", (0, -1, True, 1.5))
def test_invalid_capacity_is_rejected(max_entries: object) -> None:
    with pytest.raises(ValueError):
        InMemoryIdempotencyStore(max_entries=max_entries)
