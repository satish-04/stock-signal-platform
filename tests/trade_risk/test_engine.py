from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from app.services.trade_risk import RiskLimits, TradeConstructionRequest, TradeRiskEngine


def build_request(**overrides: object) -> TradeConstructionRequest:
    request = TradeConstructionRequest(
        symbol="AAPL",
        option_symbol="AAPL  260918C00100000",
        option_type="CALL",
        expiry="2026-09-18",
        strike=Decimal(100),
        multiplier=100,
        bid=Decimal("4.90"),
        ask=Decimal("5.10"),
        last=Decimal("5.00"),
        volume=1500,
        open_interest=6000,
        action="BUY_CALL",
        confidence=Decimal(90),
        stop_loss_pct=Decimal(20),
        first_target_pct=Decimal(40),
        second_target_pct=Decimal(80),
    )
    return replace(request, **overrides)


def build_limits(**overrides: object) -> RiskLimits:
    limits = RiskLimits(
        account_equity=Decimal(100000),
        available_funds=Decimal(50000),
        max_risk_per_trade_pct=Decimal("1.00"),
        max_position_value_pct=Decimal("2.00"),
        max_contracts=5,
        max_bid_ask_spread_pct=Decimal("5.00"),
        minimum_open_interest=1000,
        minimum_volume=250,
        minimum_reward_risk_ratio=Decimal("2.00"),
    )
    return replace(limits, **overrides)


def test_approved_trade_plan() -> None:
    plan = TradeRiskEngine.construct(build_request(), build_limits())
    assert plan.decision == "APPROVED"
    assert plan.symbol == "AAPL"
    assert plan.side == "BUY"
    assert plan.order_type == "LIMIT"
    assert plan.quantity == 2
    assert plan.limit_price == Decimal("5.00")
    assert plan.estimated_debit == Decimal("1000.00")
    assert plan.maximum_loss == Decimal("1000.00")
    assert plan.stop_price == Decimal("4.00")
    assert plan.first_target_price == Decimal("7.00")
    assert plan.second_target_price == Decimal("9.00")
    assert plan.reward_risk_ratio == Decimal("2.00")
    assert plan.account_risk_pct == Decimal("1.00")
    assert plan.bid_ask_spread_pct == Decimal("4.00")
    assert not plan.rejection_reasons


def test_symbol_is_normalized() -> None:
    plan = TradeRiskEngine.construct(build_request(symbol=" aapl "), build_limits())
    assert plan.symbol == "AAPL"


def test_midpoint_is_rounded_to_cent() -> None:
    request = build_request(bid=Decimal("4.91"), ask=Decimal("5.02"))
    plan = TradeRiskEngine.construct(
        request, build_limits(max_bid_ask_spread_pct=Decimal(10))
    )
    assert plan.limit_price == Decimal("4.97")


@pytest.mark.parametrize(
    ("limits", "quantity", "debit"),
    [
        ({"max_risk_per_trade_pct": Decimal("0.50")}, 1, Decimal("500.00")),
        (
            {
                "max_risk_per_trade_pct": Decimal(5),
                "max_position_value_pct": Decimal("0.50"),
            },
            1,
            Decimal("500.00"),
        ),
        (
            {
                "max_risk_per_trade_pct": Decimal(5),
                "max_position_value_pct": Decimal(5),
                "available_funds": Decimal(750),
            },
            1,
            Decimal("500.00"),
        ),
        (
            {
                "max_risk_per_trade_pct": Decimal(10),
                "max_position_value_pct": Decimal(10),
                "max_contracts": 1,
            },
            1,
            Decimal("500.00"),
        ),
    ],
)
def test_quantity_constraints(
    limits: dict[str, object], quantity: int, debit: Decimal
) -> None:
    plan = TradeRiskEngine.construct(build_request(), build_limits(**limits))
    assert plan.quantity == quantity
    assert plan.estimated_debit == debit
    assert plan.maximum_loss == debit


@pytest.mark.parametrize(
    ("request_overrides", "reason"),
    [
        ({"action": "HOLD"}, "HOLD recommendations cannot create an order."),
        (
            {"option_type": "PUT", "action": "BUY_CALL"},
            "Selected option type does not match the recommended action.",
        ),
        (
            {"option_type": "CALL", "action": "BUY_PUT"},
            "Selected option type does not match the recommended action.",
        ),
        (
            {"bid": Decimal(4), "ask": Decimal(6)},
            "Bid/ask spread exceeds the configured limit.",
        ),
        (
            {"open_interest": 500},
            "Open interest is below the configured minimum.",
        ),
        ({"volume": 100}, "Volume is below the configured minimum."),
    ],
)
def test_policy_rejections(request_overrides: dict[str, object], reason: str) -> None:
    plan = TradeRiskEngine.construct(build_request(**request_overrides), build_limits())
    assert plan.decision == "REJECTED"
    assert reason in plan.rejection_reasons


def test_reward_risk_below_minimum_is_rejected() -> None:
    request = build_request(first_target_pct=Decimal(20), second_target_pct=Decimal(40))
    plan = TradeRiskEngine.construct(
        request, build_limits(minimum_reward_risk_ratio=Decimal("1.50"))
    )
    assert plan.reward_risk_ratio == Decimal("1.00")
    assert plan.decision == "REJECTED"


def test_cannot_afford_one_contract_is_rejected() -> None:
    limits = build_limits(
        account_equity=Decimal(10000),
        available_funds=Decimal(100),
        max_risk_per_trade_pct=Decimal(1),
        max_position_value_pct=Decimal(2),
    )
    plan = TradeRiskEngine.construct(build_request(), limits)
    assert plan.quantity == 0
    assert plan.maximum_loss == Decimal("0.00")
    assert plan.decision == "REJECTED"


def test_high_confidence_does_not_override_risk_rejection() -> None:
    plan = TradeRiskEngine.construct(
        build_request(confidence=Decimal(100), volume=0), build_limits()
    )
    assert plan.decision == "REJECTED"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("symbol", "", "symbol must not be empty"),
        ("option_symbol", "", "option_symbol must not be empty"),
        ("multiplier", 0, "multiplier must be greater than zero"),
        ("bid", Decimal("-0.01"), "bid must not be negative"),
        ("ask", Decimal(0), "ask must be greater than zero"),
        ("last", Decimal("-0.01"), "last must not be negative"),
        ("volume", -1, "volume must not be negative"),
        ("open_interest", -1, "open_interest must not be negative"),
        ("confidence", Decimal(101), "confidence must be between 0 and 100"),
        ("stop_loss_pct", Decimal(0), "stop_loss_pct must be between 0 and 100"),
        ("first_target_pct", Decimal(0), "first_target_pct must be greater than zero"),
    ],
)
def test_invalid_request_values(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TradeRiskEngine.construct(build_request(**{field: value}), build_limits())


def test_ask_below_bid_is_rejected() -> None:
    with pytest.raises(ValueError, match="ask must be greater than or equal to bid"):
        TradeRiskEngine.construct(
            build_request(bid=Decimal("5.10"), ask=Decimal("4.90")), build_limits()
        )


def test_second_target_must_exceed_first_target() -> None:
    with pytest.raises(ValueError, match="second_target_pct must be greater"):
        TradeRiskEngine.construct(
            build_request(first_target_pct=Decimal(40), second_target_pct=Decimal(40)),
            build_limits(),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("account_equity", Decimal(0), "account_equity must be greater than zero"),
        ("available_funds", Decimal(-1), "available_funds must not be negative"),
        ("max_risk_per_trade_pct", Decimal(0), "max_risk_per_trade_pct must be"),
        ("max_position_value_pct", Decimal(101), "max_position_value_pct must be"),
        ("max_contracts", 0, "max_contracts must be greater than zero"),
        ("max_bid_ask_spread_pct", Decimal(-1), "must not be negative"),
        ("minimum_open_interest", -1, "must not be negative"),
        ("minimum_volume", -1, "minimum_volume must not be negative"),
        ("minimum_reward_risk_ratio", Decimal(0), "must be greater than zero"),
    ],
)
def test_invalid_limit_values(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        TradeRiskEngine.construct(build_request(), build_limits(**{field: value}))
