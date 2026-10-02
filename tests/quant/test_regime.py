import math

import pytest

from app.services.quant import regime, service


def trend(bars: int, drift: float, wobble: float = 0.002) -> list[float]:
    return [100 * (1 + drift) ** i * (1 + wobble * math.sin(i)) for i in range(bars)]


def test_rising_market_is_an_uptrend_that_favours_bullish_trades():
    result = regime.classify(trend(400, 0.001))
    assert result["trend"] == "up"
    assert result["scores"]["bullish"] > result["scores"]["bearish"]


def test_falling_market_is_a_downtrend_that_favours_bearish_trades():
    result = regime.classify(trend(400, -0.001))
    assert result["trend"] == "down"
    assert result["scores"]["bearish"] > result["scores"]["bullish"]


def test_recent_turbulence_is_flagged_as_high_volatility():
    closes = trend(380, 0.001) + [trend(380, 0.001)[-1] * (1 + 0.04 * (-1) ** i) for i in range(20)]
    assert regime.classify(closes)["volatility"] == "high"


def test_too_little_history_gives_no_regime():
    assert regime.classify(trend(regime.MIN_BARS - 1, 0.001)) is None


@pytest.mark.parametrize(
    "trend_name, volatility, direction, expected",
    [
        ("up", "normal", "bullish", 85.0),
        ("up", "normal", "bearish", 30.0),
        ("down", "normal", "bearish", 85.0),
        ("mixed", "normal", "bullish", 60.0),
        ("up", "high", "bullish", 70.0),
        ("down", "high", "bullish", 15.0),
    ],
)
def test_regime_score(trend_name, volatility, direction, expected):
    assert regime.score_for(trend_name, volatility, direction) == expected


async def test_scoring_uses_the_fixed_default_unless_enabled(monkeypatch):
    async def explode(symbol):
        raise AssertionError("must not fetch when disabled")

    monkeypatch.setattr(service, "market_regime", explode)
    assert await service.regime_for_scoring("bullish") == (70.0, None)


async def test_scoring_uses_the_regime_when_enabled(monkeypatch):
    monkeypatch.setattr(service.get_settings(), "regime_scoring_enabled", True)
    found = {"trend": "down", "scores": {"bullish": 30.0, "bearish": 85.0}}

    async def fake(symbol):
        return found

    monkeypatch.setattr(service, "market_regime", fake)
    assert await service.regime_for_scoring("bullish") == (30.0, found)
    assert await service.regime_for_scoring("neutral") == (70.0, None)


async def test_scoring_falls_back_to_the_default_when_data_is_unavailable(monkeypatch):
    monkeypatch.setattr(service.get_settings(), "regime_scoring_enabled", True)

    async def broken(symbol):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(service, "market_regime", broken)
    assert await service.regime_for_scoring("bearish") == (70.0, None)
