from datetime import UTC, datetime
from decimal import Decimal

from app.services.order_execution import OrderExecution, RedisOrderExecutionStore


def execution() -> OrderExecution:
    now = datetime.now(UTC)
    return OrderExecution(
        execution_id="execution-1",
        intent_id="intent-1",
        idempotency_key="idem-1",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="BUY",
        order_type="LIMIT",
        requested_quantity=2,
        limit_price=Decimal("5.00"),
        status="SUBMITTED",
        broker_order_id="paper-1",
        broker_status="simulated",
        filled_quantity=0,
        remaining_quantity=2,
        average_fill_price=None,
        submitted_at=now,
        acknowledged_at=None,
        completed_at=None,
        created_at=now,
        updated_at=now,
        status_reason=None,
        broker_response={"status": "simulated"},
    )


def test_redis_serialization_round_trip() -> None:
    expected = execution()
    restored = RedisOrderExecutionStore._deserialize(
        RedisOrderExecutionStore._serialize(expected)
    )
    assert restored == expected
    assert isinstance(restored.limit_price, Decimal)
