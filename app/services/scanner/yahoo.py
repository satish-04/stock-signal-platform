import math
import tempfile
from pathlib import Path
from typing import Any

import structlog

from app.services.scanner.engine import ChainSnapshot, OptionQuote, Right


def _number(value: Any) -> float:
    """Coerce Yahoo's NaN, None and infinite values to 0 so results stay valid JSON."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return 0.0
    return number if math.isfinite(number) else 0.0


class YahooOptionsProvider:
    """Read-only option chains from Yahoo Finance. All calls block; run them in a thread."""

    screens = ("most_actives", "day_gainers", "day_losers")

    def __init__(self) -> None:
        # Imported here, not at module level, so a problem with this one dependency fails
        # a scan instead of stopping the whole API from starting.
        import yfinance

        self._yf = yfinance
        # The API container runs as a user without a home directory, so yfinance's default
        # cache location is not writable there.
        yfinance.set_tz_cache_location(str(Path(tempfile.gettempdir()) / "yfinance-cache"))

    def screen_symbols(self, count: int = 25) -> list[str]:
        log = structlog.get_logger()
        symbols: list[str] = []
        for screen in self.screens:
            try:
                quotes = self._yf.screen(screen, count=count)["quotes"]
            except Exception:  # noqa: BLE001 - screens only widen the universe
                log.warning("options_scan_screen_failed", screen=screen)
                continue
            symbols.extend(quote["symbol"] for quote in quotes)
        return symbols

    def chain(self, symbol: str, expiry: str) -> ChainSnapshot | None:
        """Return the chain for ``expiry``, or None when the symbol does not list it."""
        ticker = self._yf.Ticker(symbol)
        if expiry not in ticker.options:
            return None
        chain = ticker.option_chain(expiry)
        quotes = [*self._quotes(chain.calls, "C"), *self._quotes(chain.puts, "P")]
        traded = [
            frame.lastTradeDate.max()
            for frame in (chain.calls, chain.puts)
            if not frame.empty and frame.lastTradeDate.notna().any()
        ]
        return ChainSnapshot(
            symbol=symbol,
            expiry=expiry,
            spot=_number(chain.underlying.get("regularMarketPrice")),
            change_pct=_number(chain.underlying.get("regularMarketChangePercent")),
            quotes=quotes,
            last_trade_at=max(traded).isoformat() if traded else None,
        )

    @staticmethod
    def _quotes(frame: Any, right: Right) -> list[OptionQuote]:
        return [
            OptionQuote(
                strike=_number(row.strike),
                right=right,
                last=_number(row.lastPrice),
                bid=_number(row.bid),
                ask=_number(row.ask),
                volume=int(_number(row.volume)),
                open_interest=int(_number(row.openInterest)),
            )
            for row in frame.itertuples()
        ]
