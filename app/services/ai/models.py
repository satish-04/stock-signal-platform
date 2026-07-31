from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

TradeAction = Literal[
    "BUY_CALL",
    "BUY_PUT",
    "SELL_CALL",
    "SELL_PUT",
    "HOLD",
]


RiskLevel = Literal[
    "LOW",
    "MEDIUM",
    "HIGH",
]


OptionType = Literal[
    "CALL",
    "PUT",
]


@dataclass(frozen=True)
class SelectedOptionContract:
    symbol: str
    expiry: str
    strike: Decimal
    option_type: OptionType
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    selection_score: float
    selection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class RecommendedTradePlan:
    decision: Literal["APPROVED", "REJECTED"]
    side: Literal["BUY", "SELL"]
    order_type: Literal["LIMIT"]
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


@dataclass(frozen=True)
class AIRecommendation:
    symbol: str

    action: TradeAction

    confidence: float

    risk: RiskLevel

    entry: str

    stop_loss: str

    targets: tuple[str, ...]

    position_size_pct: float

    summary: str

    pros: tuple[str, ...]

    cons: tuple[str, ...]

    reasoning: str

    selected_option: SelectedOptionContract | None = None
    trade_plan: RecommendedTradePlan | None = None
