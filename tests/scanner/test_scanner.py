from datetime import date, datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.scanner import OptionsScanRequest
from app.services.scanner import service
from app.services.scanner.engine import (
    ChainSnapshot,
    OptionQuote,
    OptionsScanEngine,
    greeks,
    implied_volatility,
    next_weekly_expiry,
    option_price,
    upcoming_weekly_expiry,
)

EXPIRY = "2026-10-02"  # closes 20:00 UTC
THURSDAY_AFTERNOON = datetime(2026, 10, 1, 18, 0, tzinfo=timezone.utc)  # 26 hours before the close
THURSDAY_CLOSE = "2026-10-01T20:00:00+00:00"  # 24 hours before the close
OVERNIGHT = datetime(2026, 10, 2, 6, 0, tzinfo=timezone.utc)
HOUR = 1 / (365 * 24)


def quote(strike, right, last, volume, bid=None, ask=None, open_interest=100):
    return OptionQuote(
        strike=strike,
        right=right,
        last=last,
        bid=last - 0.05 if bid is None else bid,
        ask=last + 0.05 if ask is None else ask,
        volume=volume,
        open_interest=open_interest,
    )


def chain(symbol="NVDA", spot=230.86, quotes=None, last_trade_at=None):
    if quotes is None:
        quotes = [
            quote(230, "C", 2.20, 160),
            quote(232.5, "C", 0.95, 256),
            quote(235, "C", 0.33, 218),
            quote(240, "C", 0.05, 0),
            quote(225, "P", 0.21, 67),
            quote(227.5, "P", 0.47, 111),
            quote(230, "P", 1.10, 197),
        ]
    return ChainSnapshot(
        symbol=symbol,
        expiry=EXPIRY,
        spot=spot,
        change_pct=1.09,
        quotes=quotes,
        last_trade_at=last_trade_at,
    )


def summarize(snapshot, now=THURSDAY_AFTERNOON):
    return OptionsScanEngine().summarize(snapshot, now)


def test_summary_totals_and_put_call_ratio():
    summary = summarize(chain())
    assert summary["call_volume"] == 634
    assert summary["put_volume"] == 375
    assert summary["total_volume"] == 1009
    assert summary["put_call_ratio"] == 0.59


def test_summary_uses_the_strike_nearest_spot_listed_on_both_sides():
    summary = summarize(chain())
    # 230 is the only strike with both a call and a put, and the nearest to 230.86.
    assert summary["atm_strike"] == 230
    # Straddle mid is 2.20 + 1.10 = 3.30 on a 230.86 stock.
    assert summary["implied_move_pct"] == 1.43


def test_top_strikes_are_ranked_by_volume_and_carry_premium():
    summary = summarize(chain())
    assert [strike["strike"] for strike in summary["top_calls"]] == [232.5, 235, 230]
    assert [strike["strike"] for strike in summary["top_puts"]] == [230, 227.5, 225]
    top = summary["top_calls"][0]
    assert top["volume"] == 256
    assert top["premium"] == 24320  # 256 contracts x $0.95 x 100 shares


def test_open_interest_is_unknown_when_the_whole_chain_reports_none():
    known = summarize(chain())["top_calls"][0]
    assert known["open_interest"] == 100
    blank = [quote(100, "C", 2.0, 10, open_interest=0), quote(100, "P", 1.0, 10, open_interest=0)]
    assert summarize(chain(spot=100, quotes=blank))["top_calls"][0]["open_interest"] is None


def test_untraded_strikes_are_left_out_of_top_strikes():
    assert 240 not in [strike["strike"] for strike in summarize(chain())["top_calls"]]


def test_implied_move_falls_back_to_last_price_when_quotes_are_missing():
    quotes = [quote(100, "C", 2.0, 10, bid=0, ask=0), quote(100, "P", 1.0, 10, bid=0, ask=0)]
    assert summarize(chain(spot=100, quotes=quotes))["implied_move_pct"] == 3.0


def test_put_call_ratio_is_none_without_call_volume():
    quotes = [quote(100, "C", 2.0, 0), quote(100, "P", 1.0, 10)]
    assert summarize(chain(spot=100, quotes=quotes))["put_call_ratio"] is None


@pytest.mark.parametrize(
    "spot, quotes",
    [
        (0, None),
        (100, []),
        (100, [quote(100, "C", 2.0, 10)]),
        (100, [quote(100, "C", 2.0, 10), quote(95, "P", 1.0, 10)]),
    ],
)
def test_unusable_chains_are_not_summarized(spot, quotes):
    assert summarize(chain(spot=spot, quotes=quotes)) is None


def test_option_price_matches_a_known_black_scholes_value():
    # At the money, one year, 20% volatility, zero rates: 100 * (2 * N(0.1) - 1).
    assert option_price(100, 100, 1.0, 0.2, "C") == pytest.approx(7.9656, abs=1e-4)
    assert option_price(100, 100, 1.0, 0.2, "P") == pytest.approx(7.9656, abs=1e-4)


@pytest.mark.parametrize("right, strike", [("C", 100), ("P", 100), ("C", 110), ("P", 90)])
def test_implied_volatility_recovers_the_volatility_behind_a_price(right, strike):
    price = option_price(100, strike, 0.25, 0.45, right)
    assert implied_volatility(price, 100, strike, 0.25, right) == pytest.approx(0.45, abs=1e-6)


@pytest.mark.parametrize(
    "price, years",
    [
        (10.0, 0.1),  # exactly intrinsic: no time value to explain
        (0.0, 0.1),
        (12.0, 0.0),
    ],
)
def test_implied_volatility_is_none_when_it_cannot_be_solved(price, years):
    assert implied_volatility(price, 110, 100, years, "C") is None


def test_greeks_match_known_black_scholes_values():
    # At the money, one year, 20% volatility, zero rates: d1 = 0.1.
    call = greeks(100, 100, 1.0, 0.2, "C")
    assert call["delta"] == pytest.approx(0.5398, abs=1e-4)
    assert call["gamma"] == pytest.approx(0.019848, abs=1e-5)
    assert call["vega"] == pytest.approx(0.39695, abs=1e-4)
    assert call["theta"] == pytest.approx(-0.010875, abs=1e-5)
    put = greeks(100, 100, 1.0, 0.2, "P")
    assert put["delta"] == pytest.approx(call["delta"] - 1)
    assert put["gamma"] == call["gamma"]


def test_delta_agrees_with_a_small_change_in_the_price_model():
    bump = 0.01
    change = option_price(100 + bump, 105, 0.25, 0.4, "C") - option_price(100 - bump, 105, 0.25, 0.4, "C")
    assert greeks(100, 105, 0.25, 0.4, "C")["delta"] == pytest.approx(change / (2 * bump), abs=1e-4)


def test_top_strikes_carry_delta_when_volatility_can_be_solved():
    live = summarize(chain(spot=100, quotes=atm_pair(0.5, hours=26, live=True)))
    assert live["top_calls"][0]["delta"] == pytest.approx(0.5, abs=0.02)
    assert live["top_puts"][0]["delta"] == pytest.approx(-0.5, abs=0.02)
    expired = summarize(
        chain(spot=100, quotes=atm_pair(0.5, hours=26, live=True)),
        datetime(2026, 10, 2, 20, 30, tzinfo=timezone.utc),
    )
    assert expired["top_calls"][0]["delta"] is None


def atm_pair(volatility, hours, live):
    """An at-the-money call and put priced at ``volatility`` with ``hours`` to expiry."""
    price = option_price(100, 100, hours * HOUR, volatility, "C")
    spread = {"bid": price - 0.01, "ask": price + 0.01} if live else {"bid": 0, "ask": 0}
    return [quote(100, "C", price, 50, **spread), quote(100, "P", price, 40, **spread)]


def test_atm_iv_is_solved_from_live_quotes_as_of_now():
    summary = summarize(chain(spot=100, quotes=atm_pair(0.5, hours=26, live=True)))
    assert summary["atm_iv"] == pytest.approx(0.5, abs=1e-3)
    assert summary["top_calls"][0]["implied_volatility"] == pytest.approx(0.5, abs=1e-3)


def test_atm_iv_uses_last_trades_as_of_the_last_trade_when_quotes_are_gone():
    # Overnight the bid and ask are zero. Prices are from the close, so time to expiry must
    # be measured from the close too, not from the 14 hours left when the scan runs.
    snapshot = chain(
        spot=100, quotes=atm_pair(0.5, hours=24, live=False), last_trade_at=THURSDAY_CLOSE
    )
    assert summarize(snapshot, OVERNIGHT)["atm_iv"] == pytest.approx(0.5, abs=1e-3)


def test_atm_iv_is_none_once_the_expiry_has_closed():
    after_close = datetime(2026, 10, 2, 20, 30, tzinfo=timezone.utc)
    summary = summarize(chain(spot=100, quotes=atm_pair(0.5, hours=26, live=True)), after_close)
    assert summary["atm_iv"] is None
    assert summary["implied_move_pct"] > 0


def test_iv_ranking_ignores_thin_and_unsolved_symbols():
    items = [
        {"symbol": "SPY", "total_volume": 2_000_000, "atm_iv": 0.16},
        {"symbol": "NKE", "total_volume": 290_000, "atm_iv": 2.18},
        {"symbol": "MARA", "total_volume": 150_000, "atm_iv": 0.89},
        {"symbol": "THIN", "total_volume": 900, "atm_iv": 5.0},
        {"symbol": "NOIV", "total_volume": 400_000, "atm_iv": None},
    ]
    engine = OptionsScanEngine()
    assert engine.iv_min_volume(items) == 20_000
    assert engine.rank_by_iv(items) == ["NKE", "MARA", "SPY"]


def test_iv_ranking_floor_holds_when_volume_is_light():
    engine = OptionsScanEngine()
    assert engine.iv_min_volume([{"symbol": "SPY", "total_volume": 4_000, "atm_iv": 0.2}]) == 500
    assert engine.iv_min_volume([]) == 500


@pytest.mark.parametrize(
    "today, expected",
    [
        (date(2026, 9, 28), date(2026, 10, 2)),  # Monday
        (date(2026, 10, 1), date(2026, 10, 2)),  # Thursday
        (date(2026, 10, 2), date(2026, 10, 2)),  # Friday is its own expiry
        (date(2026, 10, 3), date(2026, 10, 9)),  # Saturday rolls to next week
    ],
)
def test_next_weekly_expiry_is_the_friday_on_or_after_today(today, expected):
    assert next_weekly_expiry(today) == expected


@pytest.mark.parametrize(
    "now, expected",
    [
        (datetime(2026, 10, 1, 23, 0, tzinfo=timezone.utc), date(2026, 10, 2)),  # Thursday evening
        (datetime(2026, 10, 2, 19, 59, tzinfo=timezone.utc), date(2026, 10, 2)),  # Friday 15:59 ET
        (datetime(2026, 10, 2, 20, 0, tzinfo=timezone.utc), date(2026, 10, 9)),  # Friday at the close
        (datetime(2026, 10, 3, 2, 0, tzinfo=timezone.utc), date(2026, 10, 9)),  # Friday 22:00 ET
        (datetime(2026, 10, 3, 15, 0, tzinfo=timezone.utc), date(2026, 10, 9)),  # Saturday
    ],
)
def test_default_expiry_rolls_forward_once_an_expiry_friday_has_closed(now, expected):
    assert upcoming_weekly_expiry(now) == expected


def test_scan_request_normalizes_and_validates_symbols():
    request = OptionsScanRequest(symbols=[" nvda ", "NVDA", "^spx", "brk-b"])
    assert request.symbols == ["NVDA", "^SPX", "BRK-B"]
    assert OptionsScanRequest().symbols is None
    with pytest.raises(ValidationError):
        OptionsScanRequest(symbols=["NVDA; DROP"])
    with pytest.raises(ValidationError):
        OptionsScanRequest(symbols=[])


class FakeProvider:
    def __init__(self, chains, screened=(), failing=()):
        self.chains = chains
        self.screened = list(screened)
        self.failing = set(failing)
        self.calls = []

    def screen_symbols(self):
        return self.screened

    def chain(self, symbol, expiry):
        self.calls.append(symbol)
        if symbol in self.failing:
            raise RuntimeError("rate limited")
        return self.chains.get(symbol)


async def test_universe_adds_screened_symbols_without_duplicates():
    provider = FakeProvider({}, screened=["NVDA", "ZZZZ"])
    universe = await service.build_universe(provider, None)
    assert universe[0] == "SPY"
    assert universe.count("NVDA") == 1
    assert universe[-1] == "ZZZZ"


async def test_explicit_symbols_replace_the_default_universe():
    provider = FakeProvider({}, screened=["ZZZZ"])
    assert await service.build_universe(provider, ["TSLA", "TSLA", "AMD"]) == ["TSLA", "AMD"]


async def test_scan_orders_by_volume_and_reports_every_skipped_symbol(monkeypatch):
    monkeypatch.setattr(service, "RETRY_DELAY_SECONDS", 0)
    light = [quote(50, "C", 1.0, 5), quote(50, "P", 1.0, 5)]
    provider = FakeProvider(
        {"LIGHT": chain("LIGHT", spot=50, quotes=light), "NVDA": chain("NVDA")},
        failing=["DOWN"],
    )
    seen = []

    items, skipped = await service.scan_symbols(
        provider, ["LIGHT", "NOEXP", "NVDA", "DOWN"], EXPIRY, seen.append
    )

    assert [item["symbol"] for item in items] == ["NVDA", "LIGHT"]
    assert skipped == [
        {"symbol": "DOWN", "reason": "error: rate limited"},
        {"symbol": "NOEXP", "reason": "no chain for this expiry"},
    ]
    assert sorted(seen) == [1, 2, 3, 4]
    assert provider.calls.count("DOWN") == service.ATTEMPTS
