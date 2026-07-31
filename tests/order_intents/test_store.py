import pytest

from app.services.order_intents import (
    DuplicateOrderIntentError,
    InMemoryOrderIntentStore,
)


@pytest.mark.asyncio
async def test_register_and_contains() -> None:
    store = InMemoryOrderIntentStore()
    await store.register("key")
    assert await store.contains("key")


@pytest.mark.asyncio
async def test_duplicate_registration_is_rejected() -> None:
    store = InMemoryOrderIntentStore()
    await store.register("key")
    with pytest.raises(DuplicateOrderIntentError):
        await store.register("key")


@pytest.mark.asyncio
async def test_clear_allows_key_to_be_registered_again() -> None:
    store = InMemoryOrderIntentStore()
    await store.register("key")
    await store.clear()
    await store.register("key")
    assert await store.contains("key")
