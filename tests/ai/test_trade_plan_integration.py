from __future__ import annotations

from decimal import Decimal

import pytest

from app.services.ai.service import AIRecommendationService
from app.services.brokers.mock import MockBrokerAdapter
from app.services.indicators.models import IndicatorResult
from app.services.signals.models import TechnicalSignalResult


class StubIndicatorService:
    async def calculate_for_symbol(self, **kwargs: object) -> IndicatorResult:
        del kwargs
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


def signal(direction: str, confidence: float) -> TechnicalSignalResult:
    return TechnicalSignalResult(
        direction=direction,  # type: ignore[arg-type]
        confidence=confidence,
        trend_score=0.0,
        momentum_score=0.0,
        volatility_score=15.0,
        volume_score=10.0,
        reasons=(f"{direction} test",),
        warnings=(),
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("direction", "symbol", "action", "option_type"),
    [
        ("bullish", "aapl", "BUY_CALL", "CALL"),
        ("bearish", "msft", "BUY_PUT", "PUT"),
    ],
)
async def test_directional_recommendation_includes_trade_plan(
    monkeypatch: pytest.MonkeyPatch,
    direction: str,
    symbol: str,
    action: str,
    option_type: str,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService()
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: signal(direction, 90.0),
    )
    recommendation = await service.recommend(symbol)
    assert recommendation.action == action
    assert recommendation.selected_option is not None
    assert recommendation.selected_option.option_type == option_type
    assert recommendation.trade_plan is not None
    assert recommendation.trade_plan.side == "BUY"
    assert recommendation.trade_plan.maximum_loss >= Decimal(0)


@pytest.mark.asyncio
async def test_neutral_recommendation_has_no_trade_plan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService()
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: signal("neutral", 35.0),
    )
    recommendation = await service.recommend("nvda")
    assert recommendation.action == "HOLD"
    assert recommendation.selected_option is None
    assert recommendation.trade_plan is None


@pytest.mark.asyncio
async def test_risk_rejection_is_not_overridden_by_confidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService()
    service.settings = service.settings.model_copy(
        update={"minimum_option_volume": 10_000_000}
    )
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: signal("bullish", 100.0),
    )
    recommendation = await service.recommend("AAPL")
    assert recommendation.trade_plan is not None
    assert recommendation.trade_plan.decision == "REJECTED"


@pytest.mark.asyncio
async def test_trade_plan_evidence_is_in_ai_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = AIRecommendationService(MockBrokerAdapter())
    service.indicators = StubIndicatorService()
    monkeypatch.setattr(
        "app.services.ai.service.TechnicalSignalEngine.evaluate",
        lambda **kwargs: signal("bullish", 90.0),
    )
    recommendation = await service.recommend("AAPL")
    assert "Deterministic trade-risk plan:" in recommendation.reasoning
    assert "Maximum loss:" in recommendation.reasoning
