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
