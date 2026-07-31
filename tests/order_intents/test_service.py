from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.order_intents import (
    DuplicateOrderIntentError,
    LiveTradingBlockedError,
    OrderIntentRejectedError,
    OrderSubmissionDisabledError,
    PaperOrderApprovalService,
)
from app.services.trade_risk import RiskLimits, TradeConstructionRequest, TradeRiskEngine


class RecordingBroker:
    def __init__(self, error: Exception | None = None) -> None:
        self.orders: list[dict] = []
        self.error = error

    async def submit_order(self, order: dict) -> dict:
        self.orders.append(order)
        if self.error:
            raise self.error
        return {"broker_order_id": "paper-1"}


def approved_plan():
    request = TradeConstructionRequest(
        symbol="AAPL",
        option_symbol="AAPL  260918C00100000",
        option_type="CALL",
        expiry="2026-09-18",
        strike=Decimal(100),
        multiplier=100,
        bid=Decimal("4.90"),
        ask=Decimal("5.10"),
        last=Decimal(5),
        volume=1500,
        open_interest=6000,
        action="BUY_CALL",
        confidence=Decimal(90),
        stop_loss_pct=Decimal(20),
        first_target_pct=Decimal(40),
        second_target_pct=Decimal(80),
    )
    limits = RiskLimits(
        account_equity=Decimal(100000),
        available_funds=Decimal(50000),
        max_risk_per_trade_pct=Decimal(1),
        max_position_value_pct=Decimal(2),
        max_contracts=5,
        max_bid_ask_spread_pct=Decimal(5),
        minimum_open_interest=1000,
        minimum_volume=250,
        minimum_reward_risk_ratio=Decimal(2),
    )
    return TradeRiskEngine.construct(request, limits)


def settings(**overrides: object) -> Settings:
    return Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        order_intent_store="memory",
        **overrides,
    )


@pytest.mark.asyncio
async def test_create_intent_from_approved_plan() -> None:
    intent = await PaperOrderApprovalService(
        RecordingBroker(), settings=settings()
    ).create_intent(approved_plan())
    assert intent.status == "APPROVED"
    assert intent.intent_id.startswith("intent_")
    assert len(intent.idempotency_key) == 64
    assert intent.option_symbol == approved_plan().option_symbol


@pytest.mark.asyncio
async def test_idempotency_key_is_deterministic_and_duplicate_is_rejected() -> None:
    service = PaperOrderApprovalService(RecordingBroker(), settings=settings())
    first = await service.create_intent(approved_plan())
    with pytest.raises(DuplicateOrderIntentError):
        await service.create_intent(approved_plan())
    assert first.idempotency_key == service._idempotency_key(approved_plan())


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "plan",
    [
        replace(approved_plan(), decision="REJECTED"),
        replace(approved_plan(), quantity=0),
        replace(approved_plan(), limit_price=Decimal(0)),
        replace(approved_plan(), maximum_loss=Decimal(0)),
        replace(approved_plan(), rejection_reasons=("blocked",)),
    ],
)
async def test_invalid_plan_is_rejected(plan) -> None:
    with pytest.raises(OrderIntentRejectedError):
        await PaperOrderApprovalService(
            RecordingBroker(), settings=settings()
        ).create_intent(plan)


@pytest.mark.asyncio
async def test_submission_is_disabled_by_default() -> None:
    broker = RecordingBroker()
    service = PaperOrderApprovalService(broker, settings=settings())
    with pytest.raises(OrderSubmissionDisabledError):
        await service.submit(approved_plan())
    assert not broker.orders


@pytest.mark.asyncio
async def test_live_submission_is_always_blocked() -> None:
    broker = RecordingBroker()
    service = PaperOrderApprovalService(
        broker,
        settings=settings(
            trading_mode="live",
            enable_live_trading=True,
            enable_order_submission=True,
        ),
    )
    with pytest.raises(LiveTradingBlockedError):
        await service.submit(approved_plan())
    assert not broker.orders


@pytest.mark.asyncio
async def test_enabled_paper_submission_is_non_transmitting() -> None:
    broker = RecordingBroker()
    service = PaperOrderApprovalService(
        broker, settings=settings(enable_order_submission=True)
    )
    result = await service.submit(approved_plan())
    assert result.intent.status == "SUBMITTED"
    assert result.broker_response == {"broker_order_id": "paper-1"}
    assert broker.orders[0]["transmit"] is False
    assert broker.orders[0]["trading_mode"] == "paper"


@pytest.mark.asyncio
async def test_broker_failure_is_returned_as_failed_intent() -> None:
    service = PaperOrderApprovalService(
        RecordingBroker(RuntimeError("broker unavailable")),
        settings=settings(enable_order_submission=True),
    )
    result = await service.submit(approved_plan())
    assert result.intent.status == "FAILED"
    assert result.broker_response == {"error": "broker unavailable"}
