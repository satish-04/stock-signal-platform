from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.broker_events import (
    BrokerEventService,
    BrokerExecutionPayload,
    BrokerOrderStatusPayload,
    InMemoryBrokerEventStore,
)
from app.services.order_execution import InMemoryOrderExecutionStore, PaperOrderExecutionService
from app.services.order_intents import OrderIntent
from app.services.positions import InMemoryPositionStore, PaperPositionService
from app.services.positions.service import trading_day
from app.services.risk.entry_guard import EntryGuard

NOW = datetime(2026, 10, 16, 15, 0, tzinfo=UTC)


class Broker:
    async def submit_order(self, order: dict) -> dict:
        return {"status": "simulated", "broker_order_id": f"paper-{order['intent_id']}"}

    async def cancel_order(self, order: dict) -> dict:
        return {"status": "cancelled"}


def settings() -> Settings:
    return Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        enable_order_submission=True,
        position_store="memory",
        worker_max_retries=2,
    )


class Harness:
    def __init__(self) -> None:
        config = settings()
        self.positions_store = InMemoryPositionStore()
        self.executions = PaperOrderExecutionService(
            Broker(), InMemoryOrderExecutionStore(), config,
            EntryGuard(self.positions_store, config),
        )
        self.positions = PaperPositionService(self.positions_store, config)
        self.events = InMemoryBrokerEventStore()
        self.service = BrokerEventService(self.events, self.executions, self.positions, config)

    async def submitted(self, intent_id: str = "intent-1", side: str = "BUY", quantity: int = 2):
        execution = await self.executions.create(intent(intent_id, side, quantity))
        return await self.executions.submit(execution.execution_id)


def intent(intent_id: str, side: str, quantity: int) -> OrderIntent:
    return OrderIntent(
        intent_id, f"idem-{intent_id}", "AAPL", "AAPL-CALL", side, "LIMIT", quantity,
        Decimal(5), Decimal(1000), Decimal(1000), Decimal(4), Decimal(7), Decimal(9),
        "APPROVED", NOW, ("approved",), (),
    )


def report(broker_order_id: str, exec_id: str, qty: int, cumulative: int, price: str = "5",
           side: str = "BUY") -> BrokerExecutionPayload:
    return BrokerExecutionPayload(
        broker_order_id=broker_order_id, execution_id=exec_id, account_id="PAPER1",
        symbol="AAPL", option_symbol="AAPL-CALL", side=side, quantity=Decimal(qty),
        fill_price=Decimal(price), cumulative_quantity=Decimal(cumulative),
        average_price=Decimal(price), exchange="SIM", execution_time=NOW,
        permanent_id=None, client_id=None,
    )


def status(broker_order_id: str, raw: str, normalized: str) -> BrokerOrderStatusPayload:
    return BrokerOrderStatusPayload(
        broker_order_id, raw, normalized, Decimal(0), Decimal(2), None,
        None, None, None, None, None, None,
    )


@pytest.mark.asyncio
async def test_partial_then_full_fill_updates_execution_and_position() -> None:
    h = Harness()
    order = await h.submitted()
    first = await h.service.ingest_execution(report(order.broker_order_id, "e1", 1, 1))
    assert first.event.status == "PROCESSED"
    assert first.execution_status == "PARTIALLY_FILLED"
    second = await h.service.ingest_execution(report(order.broker_order_id, "e2", 1, 2))
    assert second.execution_status == "FILLED"
    [position] = await h.positions.list_positions("PAPER1")
    assert position.quantity == 2
    assert position.status == "OPEN"


@pytest.mark.asyncio
async def test_replayed_execution_report_changes_nothing() -> None:
    h = Harness()
    order = await h.submitted()
    await h.service.ingest_execution(report(order.broker_order_id, "e1", 2, 2))
    replay = await h.service.ingest_execution(report(order.broker_order_id, "e1", 2, 2))
    assert replay.message.startswith("Duplicate")
    [position] = await h.positions.list_positions("PAPER1")
    assert position.quantity == 2


@pytest.mark.asyncio
async def test_closing_fill_books_realized_pnl_for_the_day() -> None:
    h = Harness()
    buy = await h.submitted()
    await h.service.ingest_execution(report(buy.broker_order_id, "e1", 2, 2, "5"))
    sell = await h.submitted("intent-2", "SELL")
    result = await h.service.ingest_execution(
        report(sell.broker_order_id, "e2", 2, 2, "3", side="SELL")
    )
    assert result.event.status == "PROCESSED"
    [position] = await h.positions.list_positions("PAPER1")
    assert position.status == "CLOSED"
    realized = await h.positions_store.get_realized_pnl("PAPER1", trading_day(NOW))
    assert realized == Decimal("-400.00")


@pytest.mark.asyncio
async def test_unknown_broker_order_fails_for_retry() -> None:
    h = Harness()
    result = await h.service.ingest_execution(report("paper-missing", "e1", 1, 1))
    assert result.event.status == "FAILED"
    assert result.event.retryable


@pytest.mark.asyncio
async def test_mismatched_report_is_dead_lettered() -> None:
    h = Harness()
    order = await h.submitted()
    result = await h.service.ingest_execution(
        report(order.broker_order_id, "e1", 1, 1, side="SELL")
    )
    assert result.event.status == "DEAD_LETTER"
    assert (await h.executions.get(order.execution_id)).status == "SUBMITTED"


@pytest.mark.asyncio
async def test_overfill_is_dead_lettered() -> None:
    h = Harness()
    order = await h.submitted()
    result = await h.service.ingest_execution(report(order.broker_order_id, "e1", 3, 3))
    assert result.event.status == "DEAD_LETTER"


@pytest.mark.asyncio
async def test_order_status_acknowledges_then_cancels() -> None:
    h = Harness()
    order = await h.submitted()
    acked = await h.service.ingest_order_status(
        status(order.broker_order_id, "Submitted", "SUBMITTED")
    )
    assert acked.execution_status == "ACKNOWLEDGED"
    cancelled = await h.service.ingest_order_status(
        status(order.broker_order_id, "Cancelled", "CANCELLED")
    )
    assert cancelled.execution_status == "CANCELLED"


@pytest.mark.asyncio
async def test_order_status_that_does_not_apply_is_skipped() -> None:
    h = Harness()
    order = await h.submitted()
    result = await h.service.ingest_order_status(
        status(order.broker_order_id, "Filled", "FILLED")
    )
    assert result.event.status == "SKIPPED"
    assert (await h.executions.get(order.execution_id)).status == "SUBMITTED"
