from datetime import UTC, datetime
from decimal import Decimal

from app.services.position_exits import PositionExitSignal, RedisPositionExitStore


def test_signal_serialization_round_trip() -> None:
    now = datetime.now(UTC)
    signal = PositionExitSignal(
        "exit-1",
        "key-1",
        "position-1",
        "paper",
        "AAPL",
        "AAPL-CALL",
        "STOP_LOSS",
        "IMMEDIATE",
        "APPROVED",
        2,
        Decimal(4),
        Decimal(4),
        now,
        now,
        ("stop",),
        (),
    )
    restored = RedisPositionExitStore._deserialize(RedisPositionExitStore._serialize(signal))
    assert restored == signal
