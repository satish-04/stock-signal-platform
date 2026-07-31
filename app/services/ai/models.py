from __future__ import annotations

from dataclasses import dataclass
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
