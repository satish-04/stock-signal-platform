from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.services.position_exits import (
    PositionExitContext,
    PositionExitEngine,
    PositionExitRules,
)

NOW = datetime(2026, 8, 1, 12, tzinfo=UTC)


def rules() -> PositionExitRules:
    return PositionExitRules(
        Decimal(20),
        Decimal(40),
        Decimal(80),
        Decimal(50),
        True,
        Decimal(30),
        Decimal(15),
        120,
        2,
        300,
    )


def context(**changes) -> PositionExitContext:
    base = PositionExitContext(
        "position-1",
        "paper",
        "AAPL",
        "AAPL-CALL",
        4,
        100,
        Decimal(5),
        Decimal(5),
        Decimal(5),
        NOW - timedelta(hours=2),
        NOW,
        NOW - timedelta(seconds=10),
        NOW + timedelta(days=10),
        False,
    )
    return replace(base, **changes)


def test_no_trigger() -> None:
    assert not PositionExitEngine.evaluate(context(), rules()).triggered


def test_stop_loss_full_exit() -> None:
    result = PositionExitEngine.evaluate(context(current_mark_price=Decimal(4)), rules())
    assert result.reason == "STOP_LOSS"
    assert result.exit_quantity == 4


def test_first_target_partial_exit() -> None:
    result = PositionExitEngine.evaluate(
        context(current_mark_price=Decimal(7), highest_mark_price=Decimal(7)), rules()
    )
    assert result.reason == "FIRST_TARGET"
    assert result.exit_quantity == 2


def test_second_target_full_exit() -> None:
    result = PositionExitEngine.evaluate(
        context(current_mark_price=Decimal(9), highest_mark_price=Decimal(9)), rules()
    )
    assert result.reason == "SECOND_TARGET"
    assert result.exit_quantity == 4


def test_trailing_stop_after_activation() -> None:
    result = PositionExitEngine.evaluate(
        context(
            current_mark_price=Decimal("6.75"),
            highest_mark_price=Decimal(8),
            first_target_already_taken=True,
        ),
        rules(),
    )
    assert result.reason == "TRAILING_STOP"


def test_stale_mark_has_highest_priority() -> None:
    result = PositionExitEngine.evaluate(
        context(current_mark_price=Decimal(4), mark_updated_at=NOW - timedelta(seconds=301)),
        rules(),
    )
    assert result.reason == "STALE_MARK"


def test_expiration_risk_full_exit() -> None:
    result = PositionExitEngine.evaluate(context(expiration=NOW + timedelta(days=1)), rules())
    assert result.reason == "EXPIRATION_RISK"


def test_max_holding_time_full_exit() -> None:
    result = PositionExitEngine.evaluate(context(opened_at=NOW - timedelta(hours=121)), rules())
    assert result.reason == "MAX_HOLDING_TIME"
