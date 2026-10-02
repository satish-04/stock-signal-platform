"""Market regime from an index's daily closes: trend direction and volatility state."""
import math
from typing import Any

from app.services.quant.backtest import TRADING_DAYS

MIN_BARS = 260
HIGH_VOL_PERCENTILE = 0.7


def _sma(values: list[float], period: int) -> float:
    return sum(values[-period:]) / period


def _realized_vol(closes: list[float], end: int, window: int = 20) -> float:
    returns = [math.log(closes[i] / closes[i - 1]) for i in range(end - window + 1, end + 1)]
    mean = sum(returns) / window
    return math.sqrt(sum((r - mean) ** 2 for r in returns) / (window - 1) * TRADING_DAYS)


def classify(closes: list[float]) -> dict[str, Any] | None:
    """Return the regime, or None when there is too little history to judge."""
    if len(closes) < MIN_BARS:
        return None
    last, sma50, sma200 = closes[-1], _sma(closes, 50), _sma(closes, 200)
    if last > sma200 and sma50 > sma200:
        trend = "up"
    elif last < sma200 and sma50 < sma200:
        trend = "down"
    else:
        trend = "mixed"
    end = len(closes) - 1
    vols = [_realized_vol(closes, i) for i in range(end - TRADING_DAYS + 1, end + 1)]
    percentile = sum(v <= vols[-1] for v in vols) / len(vols)
    volatility = "high" if percentile >= HIGH_VOL_PERCENTILE else "normal"
    return {
        "trend": trend,
        "volatility": volatility,
        "label": f"{trend}trend, {volatility} volatility",
        "close": round(last, 2),
        "sma50": round(sma50, 2),
        "sma200": round(sma200, 2),
        "realized_vol_pct": round(vols[-1] * 100, 1),
        "vol_percentile": round(percentile * 100),
        "scores": {direction: score_for(trend, volatility, direction) for direction in ("bullish", "bearish")},
    }


def score_for(trend: str, volatility: str, direction: str) -> float:
    """0-100 score for how well the regime supports a trade in ``direction``.

    Trading with the trend scores 85, against it 30, and a mixed trend 60. High volatility
    takes 15 off either way: options are dearer and moves less reliable.
    """
    favourable = "up" if direction == "bullish" else "down"
    base = 85.0 if trend == favourable else 60.0 if trend == "mixed" else 30.0
    return base - (15.0 if volatility == "high" else 0.0)
