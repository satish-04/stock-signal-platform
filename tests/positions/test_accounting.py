from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.services.positions import ExecutionFill, PositionAccountingEngine, PositionAccountingError


def fill(**changes) -> ExecutionFill:
    base = ExecutionFill(
        fill_id="fill-1",
        execution_id="execution-1",
        broker_order_id="paper-1",
        account_id="paper-account",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="BUY",
        quantity=2,
        fill_price=Decimal("5.00"),
        multiplier=100,
        filled_at=datetime(2026, 8, 1, tzinfo=UTC),
    )
    return replace(base, **changes)


def test_open_long_position() -> None:
    result = PositionAccountingEngine.open_position("position-1", fill())
    assert result.position.quantity == 2
    assert result.position.cost_basis == Decimal("1000.00")
    assert result.opened


def test_weighted_average_on_increase() -> None:
    position = PositionAccountingEngine.open_position("position-1", fill()).position
    result = PositionAccountingEngine.apply_fill(
        position, fill(fill_id="fill-2", quantity=1, fill_price=Decimal("8.00"))
    )
    assert result.position.quantity == 3
    assert result.position.average_entry_price == Decimal("6.00")
    assert result.position.cost_basis == Decimal("1800.00")


def test_partial_reduction_realizes_profit() -> None:
    position = PositionAccountingEngine.open_position("position-1", fill()).position
    result = PositionAccountingEngine.apply_fill(
        position,
        fill(fill_id="fill-2", side="SELL", quantity=1, fill_price=Decimal("7.00")),
    )
    assert result.position.quantity == 1
    assert result.realized_pnl_change == Decimal("200.00")
    assert result.position.realized_pnl == Decimal("200.00")
    assert result.reduced and not result.closed


def test_close_position_realizes_loss() -> None:
    position = PositionAccountingEngine.open_position("position-1", fill()).position
    result = PositionAccountingEngine.apply_fill(
        position,
        fill(fill_id="fill-2", side="SELL", quantity=2, fill_price=Decimal("4.00")),
    )
    assert result.position.status == "CLOSED"
    assert result.position.quantity == 0
    assert result.position.realized_pnl == Decimal("-200.00")
    assert result.closed


def test_mark_updates_unrealized_pnl() -> None:
    position = PositionAccountingEngine.open_position("position-1", fill()).position
    marked = PositionAccountingEngine.mark(position, Decimal("6.25"))
    assert marked.market_value == Decimal("1250.00")
    assert marked.unrealized_pnl == Decimal("250.00")


def test_sell_cannot_open_long_position() -> None:
    with pytest.raises(PositionAccountingError):
        PositionAccountingEngine.open_position("position-1", fill(side="SELL"))


def test_sell_cannot_exceed_position() -> None:
    position = PositionAccountingEngine.open_position("position-1", fill()).position
    with pytest.raises(PositionAccountingError):
        PositionAccountingEngine.apply_fill(position, fill(side="SELL", quantity=3))
