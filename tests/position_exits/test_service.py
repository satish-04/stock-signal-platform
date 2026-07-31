from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.position_exits import (
    DuplicatePositionExitError,
    InMemoryPositionExitStore,
    PositionExitContext,
    PositionExitMonitoringService,
)


def context() -> PositionExitContext:
    now = datetime.now(UTC)
    return PositionExitContext(
        "position-1",
        "paper",
        "AAPL",
        "AAPL-CALL",
        4,
        100,
        Decimal(5),
        Decimal(4),
        Decimal(6),
        now - timedelta(hours=2),
        now,
        now - timedelta(seconds=10),
        now + timedelta(days=10),
        False,
    )


def service() -> PositionExitMonitoringService:
    settings = Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        position_exit_store="memory",
    )
    return PositionExitMonitoringService(InMemoryPositionExitStore(), settings)


@pytest.mark.asyncio
async def test_monitor_creates_approved_signal_and_exit_intent() -> None:
    subject = service()
    signal = await subject.monitor(context())
    assert signal is not None
    assert signal.reason == "STOP_LOSS"
    assert signal.status == "APPROVED"
    intent = subject.to_order_intent(signal)
    assert intent.side == "SELL"
    assert intent.quantity == 4
    assert intent.status == "APPROVED"


@pytest.mark.asyncio
async def test_duplicate_signal_is_blocked() -> None:
    subject = service()
    await subject.monitor(context())
    with pytest.raises(DuplicatePositionExitError):
        await subject.monitor(context())


@pytest.mark.asyncio
async def test_no_trigger_creates_no_signal() -> None:
    value = context()
    value = type(value)(**{**value.__dict__, "current_mark_price": Decimal(5)})
    assert await service().monitor(value) is None
