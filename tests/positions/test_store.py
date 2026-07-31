from datetime import UTC, datetime
from decimal import Decimal

from app.services.positions import ExecutionFill, Position, RedisPositionStore


def test_position_and_fill_serialization_round_trip() -> None:
    now = datetime.now(UTC)
    position = Position(
        position_id="position-1",
        account_id="paper",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="LONG",
        status="OPEN",
        quantity=1,
        multiplier=100,
        average_entry_price=Decimal(5),
        current_mark_price=Decimal(6),
        cost_basis=Decimal(500),
        market_value=Decimal(600),
        realized_pnl=Decimal(0),
        unrealized_pnl=Decimal(100),
        opened_at=now,
        updated_at=now,
        closed_at=None,
    )
    fill = ExecutionFill(
        "fill-1", "execution-1", "paper-1", "paper", "AAPL", "AAPL-CALL",
        "BUY", 1, Decimal(5), 100, now,
    )
    assert RedisPositionStore._position(RedisPositionStore._serialize(position)) == position
    assert RedisPositionStore._fill(RedisPositionStore._serialize(fill)) == fill
