from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SignalDirection = Literal["bullish", "bearish", "neutral"]


@dataclass(frozen=True)
class TechnicalSignalResult:
    direction: SignalDirection
    confidence: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    volume_score: float
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]
