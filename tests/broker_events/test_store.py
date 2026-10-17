from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.broker_events import (
    BrokerEvent,
    BrokerExecutionPayload,
    BrokerOrderStatusPayload,
    DuplicateBrokerEventError,
    InMemoryBrokerEventStore,
)
from app.services.broker_events.store import deserialize_event, serialize_event

NOW = datetime(2026, 10, 16, 15, 0, tzinfo=UTC)


def event(payload, event_type: str = "EXECUTION_DETAILS", **changes) -> BrokerEvent:
    base = BrokerEvent(
        "event-1", "key-1", event_type, "RECEIVED", "IBKR", "paper", "paper-1", None,
        payload, 1, 3, NOW, None, None, NOW, NOW, None, None, False,
    )
    return replace(base, **changes)


def execution_payload() -> BrokerExecutionPayload:
    return BrokerExecutionPayload(
        "paper-1", "e1", "PAPER1", "AAPL", "AAPL-CALL", "BUY", Decimal(1), Decimal("5.25"),
        Decimal(1), Decimal("5.25"), None, NOW, None, 7,
    )


def test_execution_event_round_trips_through_json() -> None:
    original = event(execution_payload(), processed_at=NOW)
    assert deserialize_event(serialize_event(original)) == original


def test_order_status_event_round_trips_through_json() -> None:
    payload = BrokerOrderStatusPayload(
        "paper-1", "Submitted", "SUBMITTED", Decimal(0), Decimal(2), None,
        None, None, None, None, "held", None,
    )
    original = event(payload, "ORDER_STATUS")
    assert deserialize_event(serialize_event(original)) == original


@pytest.mark.asyncio
async def test_memory_store_reserves_once_and_indexes() -> None:
    store = InMemoryBrokerEventStore()
    await store.reserve("key-1", "event-1")
    with pytest.raises(DuplicateBrokerEventError):
        await store.reserve("key-1", "event-1")
    await store.save(event(execution_payload(), status="FAILED", execution_id="exec-1"))
    assert await store.list_ids_by_statuses(("FAILED",), limit=10) == ["event-1"]
    assert await store.list_ids_for_broker_order("paper-1", limit=10) == ["event-1"]
    assert await store.list_ids_for_execution("exec-1", limit=10) == ["event-1"]
    assert (await store.get_by_idempotency_key("key-1")).event_id == "event-1"
