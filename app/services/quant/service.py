import asyncio
import time
from typing import Any, Protocol

import structlog

from app.core.config import get_settings
from app.services.quant import regime
from app.services.quant.backtest import PriceHistory, run_backtest

DEFAULT_REGIME_SCORE = 70.0
REGIME_CACHE_SECONDS = 1800

_regime_cache: dict[str, tuple[float, dict[str, Any] | None]] = {}


class HistoryProvider(Protocol):
    def history(self, symbol: str, years: int) -> PriceHistory | None: ...


class YahooHistoryProvider:
    """Daily adjusted closes from Yahoo Finance. Blocks; run it in a thread."""

    def history(self, symbol: str, years: int) -> PriceHistory | None:
        # Imported here so a problem with this dependency cannot stop the API from starting.
        import yfinance

        frame = yfinance.Ticker(symbol).history(period=f"{years}y", interval="1d", auto_adjust=True)
        frame = frame[frame["Close"].notna() & (frame["Close"] > 0)]
        if frame.empty:
            return None
        return PriceHistory(
            symbol=symbol,
            dates=[stamp.strftime("%Y-%m-%d") for stamp in frame.index],
            closes=[float(value) for value in frame["Close"]],
        )


async def backtest(
    symbol: str, strategy: str, years: int, cost_bps: float, provider: HistoryProvider | None = None
) -> dict[str, Any] | None:
    provider = provider or YahooHistoryProvider()
    history = await asyncio.to_thread(provider.history, symbol, years)
    if history is None or len(history.closes) < 250:
        return None
    return await asyncio.to_thread(run_backtest, history, strategy, cost_bps)


async def market_regime(symbol: str, provider: HistoryProvider | None = None) -> dict[str, Any] | None:
    """Regime for ``symbol``, cached so the signal worker does not refetch on every signal."""
    cached = _regime_cache.get(symbol)
    if cached and time.monotonic() - cached[0] < REGIME_CACHE_SECONDS:
        return cached[1]
    provider = provider or YahooHistoryProvider()
    history = await asyncio.to_thread(provider.history, symbol, 2)
    result = regime.classify(history.closes) if history else None
    if result:
        result = {"symbol": symbol, "as_of": history.dates[-1], **result}
    _regime_cache[symbol] = (time.monotonic(), result)
    return result


async def regime_for_scoring(direction: str) -> tuple[float, dict[str, Any] | None]:
    """Regime score for the signal engine. Returns the fixed default unless enabled.

    Any failure also falls back to the default: a data outage must not block or distort
    signal evaluation.
    """
    settings = get_settings()
    if not settings.regime_scoring_enabled or direction not in ("bullish", "bearish"):
        return DEFAULT_REGIME_SCORE, None
    try:
        result = await market_regime(settings.regime_index_symbol)
    except Exception:
        structlog.get_logger().warning("regime_lookup_failed", symbol=settings.regime_index_symbol)
        return DEFAULT_REGIME_SCORE, None
    if result is None:
        return DEFAULT_REGIME_SCORE, None
    return result["scores"][direction], result
