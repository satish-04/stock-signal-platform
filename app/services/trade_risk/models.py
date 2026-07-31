from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

RiskDecision = Literal[
    "APPROVED",
    "REJECTED",
]

OrderSide = Literal[
    "BUY",
    "SELL",
]

OrderType = Literal[
    "LIMIT",
]


@dataclass(frozen=True)
class RiskLimits:
    account_equity: Decimal
    available_funds: Decimal
    max_risk_per_trade_pct: Decimal
    max_position_value_pct: Decimal
    max_contracts: int
    max_bid_ask_spread_pct: Decimal
    minimum_open_interest: int
    minimum_volume: int
    minimum_reward_risk_ratio: Decimal


@dataclass(frozen=True)
class TradeConstructionRequest:
    symbol: str
    option_symbol: str
    option_type: Literal["CALL", "PUT"]
    expiry: str
    strike: Decimal
    multiplier: int
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    open_interest: int
    action: Literal[
        "BUY_CALL",
        "BUY_PUT",
        "HOLD",
    ]
    confidence: Decimal
    stop_loss_pct: Decimal
    first_target_pct: Decimal
    second_target_pct: Decimal


@dataclass(frozen=True)
class TradePlan:
    symbol: str
    option_symbol: str
    decision: RiskDecision
    side: OrderSide
    order_type: OrderType
    quantity: int
    limit_price: Decimal
    estimated_debit: Decimal
    maximum_loss: Decimal
    stop_price: Decimal
    first_target_price: Decimal
    second_target_price: Decimal
    reward_risk_ratio: Decimal
    account_risk_pct: Decimal
    bid_ask_spread_pct: Decimal
    reasons: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
