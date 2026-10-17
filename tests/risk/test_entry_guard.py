from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.order_execution import InMemoryOrderExecutionStore, PaperOrderExecutionService
from app.services.order_intents import OrderIntent
from app.services.positions import InMemoryPositionStore, Position, RedisPositionStore
from app.services.positions.service import trading_day
from app.services.risk.entry_guard import EntryBlockedError, EntryGuard

NOW = datetime(2026, 10, 16, 15, 0, tzinfo=UTC)
TODAY = trading_day(NOW)


def settings(**overrides: object) -> Settings:
    values: dict[str, object] = {
        "tradingview_webhook_secret": "test-webhook-secret-123456",
        "risk_account_equity": 100000.0,
        "max_daily_loss_pct": 1.5,
        "enable_order_submission": True,
        "position_store": "memory",
    }
    values.update(overrides)
    return Settings(**values)


def position(**changes) -> Position:
    base = Position(
        "position-1", "paper", "AAPL", "AAPL-CALL", "LONG", "OPEN", 1, 100,
        Decimal(5), Decimal(4), Decimal(500), Decimal(400), Decimal(0),
        Decimal(-100), NOW, NOW, None,
    )
    return replace(base, **changes)


async def guard_with(
    realized: Decimal = Decimal(0), *positions: Position, **overrides: object
) -> EntryGuard:
    store = InMemoryPositionStore()
    for item in positions:
        await store.save_position(item)
    if realized:
        await store.save_position(position(position_id="closed", status="CLOSED"))
        await store.record_realized_pnl("paper", TODAY, "fill-x", realized)
    return EntryGuard(store, settings(**overrides))


@pytest.mark.asyncio
async def test_status_combines_realized_today_and_open_unrealized() -> None:
    guard = await guard_with(Decimal(-1000), position())
    status = await guard.status(NOW)
    assert status.realized_pnl == Decimal(-1000)
    assert status.unrealized_pnl == Decimal(-100)
    assert status.daily_loss == Decimal(1100)
    assert status.daily_loss_limit == Decimal(1500)
    assert status.entries_allowed


@pytest.mark.asyncio
async def test_closed_positions_and_other_days_do_not_count() -> None:
    store = InMemoryPositionStore()
    await store.save_position(position(status="CLOSED", unrealized_pnl=Decimal(-5000)))
    await store.record_realized_pnl("paper", "2026-10-15", "fill-old", Decimal(-5000))
    status = await EntryGuard(store, settings()).status(NOW)
    assert status.daily_loss == 0


@pytest.mark.asyncio
async def test_gains_offset_losses_and_never_go_negative() -> None:
    guard = await guard_with(Decimal(3000), position())
    status = await guard.status(NOW)
    assert status.daily_loss == 0


@pytest.mark.asyncio
async def test_loss_at_limit_blocks_buys_but_not_sells() -> None:
    guard = await guard_with(Decimal(-1500))
    assert (await guard.status(NOW)).loss_locked
    with pytest.raises(EntryBlockedError, match="Daily loss lock"):
        await guard.check("BUY", NOW)
    await guard.check("SELL", NOW)


@pytest.mark.asyncio
async def test_kill_switch_blocks_buys_but_not_sells() -> None:
    guard = await guard_with(trading_halted=True)
    with pytest.raises(EntryBlockedError, match="halted"):
        await guard.check("BUY")
    await guard.check("SELL")


def test_trading_day_uses_market_time() -> None:
    # 01:00 UTC on the 17th is still the 16th in New York.
    assert trading_day(datetime(2026, 10, 17, 1, 0, tzinfo=UTC)) == "2026-10-16"


class Broker:
    def __init__(self) -> None:
        self.orders: list[dict] = []

    async def submit_order(self, order: dict) -> dict:
        self.orders.append(order)
        return {"status": "simulated", "broker_order_id": "paper-1"}

    async def cancel_order(self, order: dict) -> dict:
        return {"status": "cancelled"}


def intent(side: str = "BUY") -> OrderIntent:
    return OrderIntent(
        "intent-1", "idem-1", "AAPL", "AAPL-CALL", side, "LIMIT", 1, Decimal(5),
        Decimal(500), Decimal(500), Decimal(4), Decimal(7), Decimal(9), "APPROVED",
        datetime.now(UTC), ("approved",), (),
    )


@pytest.mark.asyncio
async def test_execution_submit_is_blocked_before_reaching_the_broker() -> None:
    broker = Broker()
    config = settings(trading_halted=True)
    service = PaperOrderExecutionService(
        broker, InMemoryOrderExecutionStore(), config,
        EntryGuard(InMemoryPositionStore(), config),
    )
    execution = await service.create(intent())
    with pytest.raises(EntryBlockedError):
        await service.submit(execution.execution_id)
    assert broker.orders == []
    assert (await service.get(execution.execution_id)).status == "CREATED"


@pytest.mark.asyncio
async def test_execution_submit_allows_exits_when_halted() -> None:
    broker = Broker()
    config = settings(trading_halted=True)
    service = PaperOrderExecutionService(
        broker, InMemoryOrderExecutionStore(), config,
        EntryGuard(InMemoryPositionStore(), config),
    )
    execution = await service.create(intent("SELL"))
    assert (await service.submit(execution.execution_id)).status == "SUBMITTED"


class FakePipeline:
    def __init__(self, redis: "FakeRedis") -> None:
        self.redis = redis
        self.commands: list[tuple] = []

    def hset(self, key: str, field: str, value: str):
        self.commands.append((key, field, value))
        return self

    def expire(self, key: str, seconds: int):
        return self

    async def execute(self) -> None:
        for key, field, value in self.commands:
            self.redis.hashes.setdefault(key, {})[field] = value.encode()


class FakeRedis:
    def __init__(self) -> None:
        self.hashes: dict[str, dict[str, bytes]] = {}

    def pipeline(self, transaction: bool = True) -> FakePipeline:
        return FakePipeline(self)

    async def hvals(self, key: str) -> list[bytes]:
        return list(self.hashes.get(key, {}).values())


@pytest.mark.asyncio
async def test_redis_realized_ledger_is_idempotent_per_fill() -> None:
    store = RedisPositionStore(
        FakeRedis(), key_prefix="test", position_ttl_seconds=60, fill_lock_ttl_seconds=60
    )
    await store.record_realized_pnl("paper", TODAY, "fill-1", Decimal("-120.50"))
    await store.record_realized_pnl("paper", TODAY, "fill-1", Decimal("-120.50"))
    await store.record_realized_pnl("paper", TODAY, "fill-2", Decimal("20.25"))
    assert await store.get_realized_pnl("paper", TODAY) == Decimal("-100.25")
    assert await store.get_realized_pnl("paper", "2026-10-15") == 0

