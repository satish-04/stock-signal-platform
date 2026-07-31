from __future__ import annotations

import pytest

from app.services.ai.service import AIRecommendationService
from app.services.brokers.mock import MockBrokerAdapter


@pytest.mark.asyncio
async def test_mock_ai_recommendation() -> None:
    service = AIRecommendationService(MockBrokerAdapter())

    recommendation = await service.recommend("AAPL")

    assert recommendation.symbol == "AAPL"
    assert recommendation.action in {
        "BUY_CALL",
        "BUY_PUT",
        "SELL_CALL",
        "SELL_PUT",
        "HOLD",
    }
    assert 0.0 <= recommendation.confidence <= 100.0
    assert recommendation.summary != ""
    assert recommendation.reasoning != ""


@pytest.mark.asyncio
async def test_mock_ai_recommendation_contains_prompt() -> None:
    service = AIRecommendationService(MockBrokerAdapter())

    recommendation = await service.recommend("MSFT")

    assert "MSFT" in recommendation.reasoning


@pytest.mark.asyncio
async def test_ai_service_returns_dataclass() -> None:
    service = AIRecommendationService(MockBrokerAdapter())

    recommendation = await service.recommend("NVDA")

    assert hasattr(recommendation, "action")
    assert hasattr(recommendation, "confidence")
    assert hasattr(recommendation, "reasoning")
