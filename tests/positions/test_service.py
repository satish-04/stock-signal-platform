from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.order_execution import OrderExecution
from app.services.positions import (
    DuplicateExecutionFillError,
    ExecutionFill,
    InMemoryPositionStore,
    PaperPositionService,
    PositionExecutionError,
)


def settings() -> Settings:
    return Settings(tradingview_webhook_secret="test-webhook-secret-123456")


def execution(**changes) -> OrderExecution:
    now = datetime.now(UTC)
    base = OrderExecution(
        execution_id="execution-1",
        intent_id="intent-1",
        idempotency_key="idem-1",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="BUY",
        order_type="LIMIT",
        requested_quantity=2,
        limit_price=Decimal(5),
        status="FILLED",
        broker_order_id="paper-1",
        broker_status="filled",
        filled_quantity=2,
        remaining_quantity=0,
        average_fill_price=Decimal(5),
        submitted_at=now,
        acknowledged_at=now,
        completed_at=now,
        created_at=now,
        updated_at=now,
        status_reason=None,
        broker_response={},
    )
    return replace(base, **changes)


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
        fill_price=Decimal(5),
        multiplier=100,
        filled_at=datetime.now(UTC),
    )
    return replace(base, **changes)


def service() -> PaperPositionService:
    return PaperPositionService(InMemoryPositionStore(), settings())


@pytest.mark.asyncio
async def test_process_fill_opens_position_idempotently() -> None:
    subject = service()
    result = await subject.process_fill(fill(), execution())
    assert result.opened
    assert (await subject.get(result.position.position_id)).quantity == 2
    with pytest.raises(DuplicateExecutionFillError):
        await subject.process_fill(fill(), execution())


@pytest.mark.asyncio
async def test_partial_execution_fill_is_allowed() -> None:
    subject = service()
    result = await subject.process_fill(
        fill(quantity=1),
        execution(status="PARTIALLY_FILLED", filled_quantity=1, remaining_quantity=1),
    )
    assert result.position.quantity == 1


@pytest.mark.asyncio
async def test_non_filled_execution_is_rejected() -> None:
    with pytest.raises(PositionExecutionError):
        await service().process_fill(fill(), execution(status="SUBMITTED"))


@pytest.mark.asyncio
async def test_reduce_close_mark_and_summary() -> None:
    subject = service()
    opened = await subject.process_fill(fill(), execution())
    marked = await subject.update_mark(opened.position.position_id, Decimal(6))
    assert marked.unrealized_pnl == Decimal("200.00")
    sell_execution = execution(
        execution_id="execution-2",
        intent_id="intent-2",
        side="SELL",
        broker_order_id="paper-2",
    )
    sell_fill = fill(
        fill_id="fill-2",
        execution_id="execution-2",
        side="SELL",
        broker_order_id="paper-2",
        fill_price=Decimal(7),
    )
    closed = await subject.process_fill(sell_fill, sell_execution)
    assert closed.closed
    summary = await subject.portfolio_summary("paper-account")
    assert summary["open_positions"] == 0
    assert summary["realized_pnl"] == Decimal("400.00")
