from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.order_intents import DuplicateOrderIntentError, OrderIntent
from app.services.order_intents.redis_store import RedisOrderIntentStore


class FakePipeline:
    def __init__(self, redis) -> None:
        self.redis = redis
        self.commands: list[tuple[str, object, int | None]] = []

    def set(self, key: str, value: object, ex: int | None = None):
        self.commands.append((key, value, ex))
        return self

    async def execute(self) -> list[bool]:
        for key, value, _ in self.commands:
            self.redis.data[key] = value
        return [True] * len(self.commands)


class FakeRedis:
    def __init__(self) -> None:
        self.data: dict[str, object] = {}

    async def set(self, key, value, *, nx=False, ex=None):
        if nx and key in self.data:
            return False
        self.data[key] = value
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, *keys):
        for key in keys:
            self.data.pop(key, None)

    def pipeline(self, transaction=True):
        return FakePipeline(self)


def intent() -> OrderIntent:
    return OrderIntent(
        intent_id="intent_1",
        idempotency_key="idem_1",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="BUY",
        order_type="LIMIT",
        quantity=2,
        limit_price=Decimal("5.00"),
        estimated_debit=Decimal("1000.00"),
        maximum_loss=Decimal("1000.00"),
        stop_price=Decimal("4.00"),
        first_target_price=Decimal("7.00"),
        second_target_price=Decimal("9.00"),
        status="APPROVED",
        created_at=datetime(2026, 7, 31, tzinfo=UTC),
        reasons=("risk approved",),
        rejection_reasons=(),
    )


def store(redis: FakeRedis | None = None) -> RedisOrderIntentStore:
    return RedisOrderIntentStore(
        redis or FakeRedis(),
        key_prefix="test:intents",
        intent_ttl_seconds=600,
        lock_ttl_seconds=30,
    )


@pytest.mark.asyncio
async def test_reserve_is_atomic_and_rejects_duplicate() -> None:
    subject = store()
    await subject.reserve("idem_1", "intent_1")
    with pytest.raises(DuplicateOrderIntentError):
        await subject.reserve("idem_1", "intent_2")


@pytest.mark.asyncio
async def test_save_and_get_round_trip() -> None:
    subject = store()
    expected = intent()
    await subject.reserve(expected.idempotency_key, expected.intent_id)
    await subject.save(expected)
    assert await subject.get(expected.intent_id) == expected
    assert await subject.get_by_idempotency_key(expected.idempotency_key) == expected


@pytest.mark.asyncio
async def test_delete_removes_record_and_lock() -> None:
    subject = store()
    expected = intent()
    await subject.reserve(expected.idempotency_key, expected.intent_id)
    await subject.save(expected)
    await subject.delete(expected.intent_id, expected.idempotency_key)
    assert await subject.get(expected.intent_id) is None
    assert await subject.get_by_idempotency_key(expected.idempotency_key) is None


@pytest.mark.parametrize("field", ["key_prefix", "intent_ttl_seconds", "lock_ttl_seconds"])
def test_invalid_configuration_is_rejected(field: str) -> None:
    values = {
        "key_prefix": "test",
        "intent_ttl_seconds": 60,
        "lock_ttl_seconds": 30,
    }
    values[field] = "" if field == "key_prefix" else 0
    with pytest.raises(ValueError):
        RedisOrderIntentStore(FakeRedis(), **values)


def test_serialization_preserves_decimal_and_datetime() -> None:
    expected = intent()
    restored = RedisOrderIntentStore._deserialize(
        RedisOrderIntentStore._serialize(expected)
    )
    assert restored == expected
    assert isinstance(restored.limit_price, Decimal)
    assert restored.created_at.tzinfo is not None
