from __future__ import annotations

import pytest

from app.services.ai.service import AIRecommendationService
from app.services.brokers.mock import MockBrokerAdapter
from app.services.indicators.models import IndicatorResult
from app.services.signals.models import TechnicalSignalResult


class StubIndicatorService:
    def __init__(self, result: IndicatorResult) -> None:
        self.result = result

    async def calculate_for_symbol(
        self,
        symbol: str,
        duration: str = "5 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> IndicatorResult:
        del symbol, duration, bar_size, use_rth
        return self.result


def build_indicators() -> IndicatorResult:
    return IndicatorResult(
        ema_9=110.0,
        ema_20=108.0,
        ema_50=105.0,
        ema_200=100.0,
        sma_20=108.0,
        rsi_14=62.0,
        macd=2.0,
        macd_signal=1.0,
        macd_histogram=1.0,
        atr_14=2.0,
        vwap=107.0,
        bollinger_upper=115.0,
        bollinger_middle=108.0,
        bollinger_lower=101.0,
    )


@pytest.mark.asyncio
async def test_bullish_signal_selects_best_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService(build_indicators())
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: TechnicalSignalResult(
            direction="bullish",
            confidence=90.0,
            trend_score=40.0,
            momentum_score=35.0,
            volatility_score=15.0,
            volume_score=10.0,
            reasons=("Bullish test signal.",),
            warnings=(),
        ),
    )

    recommendation = await service.recommend("aapl")

    assert recommendation.symbol == "AAPL"
    assert recommendation.action == "BUY_CALL"
    assert recommendation.selected_option is not None
    assert recommendation.selected_option.option_type == "CALL"
    assert recommendation.selected_option.symbol == "AAPL"


@pytest.mark.asyncio
async def test_bearish_signal_selects_best_put(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService(build_indicators())
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: TechnicalSignalResult(
            direction="bearish",
            confidence=88.0,
            trend_score=-40.0,
            momentum_score=-35.0,
            volatility_score=15.0,
            volume_score=10.0,
            reasons=("Bearish test signal.",),
            warnings=(),
        ),
    )

    recommendation = await service.recommend("msft")

    assert recommendation.symbol == "MSFT"
    assert recommendation.action == "BUY_PUT"
    assert recommendation.selected_option is not None
    assert recommendation.selected_option.option_type == "PUT"
    assert recommendation.selected_option.symbol == "MSFT"


@pytest.mark.asyncio
async def test_neutral_signal_selects_no_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService(build_indicators())
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: TechnicalSignalResult(
            direction="neutral",
            confidence=35.0,
            trend_score=0.0,
            momentum_score=0.0,
            volatility_score=5.0,
            volume_score=5.0,
            reasons=(),
            warnings=("Neutral test signal.",),
        ),
    )

    recommendation = await service.recommend("nvda")

    assert recommendation.symbol == "NVDA"
    assert recommendation.action == "HOLD"
    assert recommendation.selected_option is None


def test_direction_mapping_helpers() -> None:
    assert AIRecommendationService._option_type_for_direction("bullish") == "CALL"
    assert AIRecommendationService._option_type_for_direction("bearish") == "PUT"
    assert AIRecommendationService._option_type_for_direction("neutral") is None
    assert AIRecommendationService._action_for_direction("bullish") == "BUY_CALL"
    assert AIRecommendationService._action_for_direction("bearish") == "BUY_PUT"
    assert AIRecommendationService._action_for_direction("neutral") == "HOLD"
