import pytest

from app.services.order_intents import (
    DuplicateOrderIntentError,
    InMemoryOrderIntentStore,
)


def test_register_and_contains() -> None:
    store = InMemoryOrderIntentStore()
    store.register("key")
    assert store.contains("key")


def test_duplicate_registration_is_rejected() -> None:
    store = InMemoryOrderIntentStore()
    store.register("key")
    with pytest.raises(DuplicateOrderIntentError):
        store.register("key")


def test_clear_allows_key_to_be_registered_again() -> None:
    store = InMemoryOrderIntentStore()
    store.register("key")
    store.clear()
    store.register("key")
    assert store.contains("key")
