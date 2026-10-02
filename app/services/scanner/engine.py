import math
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any, Literal
from zoneinfo import ZoneInfo

Right = Literal["C", "P"]

MARKET_TIMEZONE = ZoneInfo("America/New_York")
MARKET_CLOSE = time(16, 0)
SECONDS_PER_YEAR = 365 * 24 * 3600
MIN_SECONDS_TO_EXPIRY = 300


@dataclass(frozen=True)
class OptionQuote:
    strike: float
    right: Right
    last: float
    bid: float
    ask: float
    volume: int
    open_interest: int


@dataclass(frozen=True)
class ChainSnapshot:
    symbol: str
    expiry: str
    spot: float
    change_pct: float
    quotes: list[OptionQuote]
    last_trade_at: str | None = None


def next_weekly_expiry(today: date) -> date:
    """Return the Friday on or after ``today``, the standard weekly expiration."""
    return today + timedelta(days=(4 - today.weekday()) % 7)


def upcoming_weekly_expiry(now: datetime) -> date:
    """Return the weekly expiry a scan should target at ``now``.

    Once the market has closed on an expiry Friday, that chain has expired, so an evening
    scan looks ahead to the following Friday.
    """
    local = now.astimezone(MARKET_TIMEZONE)
    expiry = next_weekly_expiry(local.date())
    if expiry == local.date() and local.time() >= MARKET_CLOSE:
        expiry += timedelta(days=7)
    return expiry


def _normal_cdf(value: float) -> float:
    return 0.5 * (1 + math.erf(value / math.sqrt(2)))


def option_price(spot: float, strike: float, years: float, volatility: float, right: Right) -> float:
    """Black-Scholes price with zero rates and dividends."""
    spread = volatility * math.sqrt(years)
    d1 = math.log(spot / strike) / spread + spread / 2
    call = spot * _normal_cdf(d1) - strike * _normal_cdf(d1 - spread)
    return call if right == "C" else call - spot + strike


def implied_volatility(
    price: float, spot: float, strike: float, years: float, right: Right
) -> float | None:
    """Volatility that reproduces ``price``, or None when the price carries no time value."""
    if min(price, spot, strike, years) <= 0:
        return None
    low, high = 0.001, 20.0
    floor = option_price(spot, strike, years, low, right)
    if price <= floor or price >= option_price(spot, strike, years, high, right):
        return None
    for _ in range(60):
        middle = (low + high) / 2
        if option_price(spot, strike, years, middle, right) < price:
            low = middle
        else:
            high = middle
    return (low + high) / 2


class OptionsScanEngine:
    """Deterministic summary of one expiry of an option chain.

    Implied volatility is solved from option prices rather than taken from the data
    provider, whose own figure collapses to zero whenever bid and ask are missing, which is
    every night after the close. Live quotes are priced at their midpoint as of now; when
    the at-the-money quotes are missing, last-trade prices are used as of the last trade.

    Implied move is the at-the-money straddle price as a percentage of spot. Contract
    counts overstate cheap far-out-of-the-money strikes, so each strike also carries the
    premium that changed hands.
    """

    top_strikes = 3
    iv_volume_share = 0.01
    iv_volume_floor = 500

    def summarize(self, chain: ChainSnapshot, now: datetime) -> dict[str, Any] | None:
        calls = {q.strike: q for q in chain.quotes if q.right == "C"}
        puts = {q.strike: q for q in chain.quotes if q.right == "P"}
        shared = sorted(calls.keys() & puts.keys())
        if chain.spot <= 0 or not shared:
            return None

        atm = min(shared, key=lambda strike: abs(strike - chain.spot))
        live = self._quoted(calls[atm]) and self._quoted(puts[atm])
        as_of = now if live or not chain.last_trade_at else datetime.fromisoformat(chain.last_trade_at)
        years = self._years_to_expiry(chain.expiry, as_of)
        atm_ivs = [
            iv for q in (calls[atm], puts[atm]) if (iv := self._iv(q, chain.spot, years)) is not None
        ]
        straddle = self._mid(calls[atm]) + self._mid(puts[atm])
        # The provider blanks open interest overnight; a chain with none at all is unknown.
        oi_known = any(q.open_interest > 0 for q in chain.quotes)
        call_volume = sum(q.volume for q in calls.values())
        put_volume = sum(q.volume for q in puts.values())
        return {
            "symbol": chain.symbol,
            "expiry": chain.expiry,
            "spot": round(chain.spot, 4),
            "change_pct": round(chain.change_pct, 2),
            "call_volume": call_volume,
            "put_volume": put_volume,
            "total_volume": call_volume + put_volume,
            "put_call_ratio": round(put_volume / call_volume, 2) if call_volume else None,
            "atm_strike": atm,
            "atm_iv": round(sum(atm_ivs) / len(atm_ivs), 4) if atm_ivs else None,
            "implied_move_pct": round(straddle / chain.spot * 100, 2),
            "top_calls": self._top(calls.values(), chain.spot, years, oi_known),
            "top_puts": self._top(puts.values(), chain.spot, years, oi_known),
            "last_trade_at": chain.last_trade_at,
        }

    def iv_min_volume(self, items: list[dict[str, Any]]) -> int:
        """Volume a symbol needs before its IV is ranked, relative to the busiest symbol.

        A relative floor keeps thinly traded chains out of the IV ranking both early in
        the session and after the close.
        """
        busiest = max((item["total_volume"] for item in items), default=0)
        return max(self.iv_volume_floor, round(busiest * self.iv_volume_share))

    def rank_by_iv(self, items: list[dict[str, Any]], limit: int = 25) -> list[str]:
        floor = self.iv_min_volume(items)
        eligible = [
            item for item in items if item["total_volume"] >= floor and item["atm_iv"] is not None
        ]
        eligible.sort(key=lambda item: item["atm_iv"], reverse=True)
        return [item["symbol"] for item in eligible[:limit]]

    def _top(
        self, quotes: Any, spot: float, years: float | None, oi_known: bool
    ) -> list[dict[str, Any]]:
        traded = sorted((q for q in quotes if q.volume > 0), key=lambda q: (-q.volume, q.strike))
        top = []
        for q in traded[: self.top_strikes]:
            iv = self._iv(q, spot, years)
            top.append(
                {
                    "strike": q.strike,
                    "volume": q.volume,
                    "open_interest": q.open_interest if oi_known else None,
                    "last": round(q.last, 2),
                    "implied_volatility": round(iv, 4) if iv is not None else None,
                    "premium": round(q.volume * q.last * 100),
                }
            )
        return top

    def _iv(self, quote: OptionQuote, spot: float, years: float | None) -> float | None:
        if years is None:
            return None
        return implied_volatility(self._mid(quote), spot, quote.strike, years, quote.right)

    @staticmethod
    def _years_to_expiry(expiry: str, as_of: datetime) -> float | None:
        close = datetime.combine(date.fromisoformat(expiry), MARKET_CLOSE, MARKET_TIMEZONE)
        seconds = (close - as_of).total_seconds()
        return seconds / SECONDS_PER_YEAR if seconds >= MIN_SECONDS_TO_EXPIRY else None

    @staticmethod
    def _quoted(quote: OptionQuote) -> bool:
        return quote.bid > 0 and quote.ask > 0

    @classmethod
    def _mid(cls, quote: OptionQuote) -> float:
        return (quote.bid + quote.ask) / 2 if cls._quoted(quote) else quote.last
