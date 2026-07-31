from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Candle:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class IndicatorResult:
    ema_9: float | None
    ema_20: float | None
    ema_50: float | None
    ema_200: float | None
    sma_20: float | None
    rsi_14: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None
    atr_14: float | None
    vwap: float | None
    bollinger_upper: float | None
    bollinger_middle: float | None
    bollinger_lower: float | None
