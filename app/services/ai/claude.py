from __future__ import annotations

from abc import ABC, abstractmethod

from app.services.ai.models import AIRecommendation


class ClaudeClient(ABC):
    @abstractmethod
    async def recommend(
        self,
        prompt: str,
    ) -> AIRecommendation:
        raise NotImplementedError


class MockClaudeClient(ClaudeClient):
    async def recommend(
        self,
        prompt: str,
    ) -> AIRecommendation:
        return AIRecommendation(
            symbol="AAPL",
            action="BUY_CALL",
            confidence=91.0,
            risk="MEDIUM",
            entry="302.00-303.00",
            stop_loss="298.50",
            targets=("307.00", "311.00", "315.00"),
            position_size_pct=2.0,
            summary="Mock recommendation generated.",
            pros=(
                "Bullish EMA alignment",
                "Positive MACD",
                "Strong relative volume",
            ),
            cons=(
                "Near resistance",
            ),
            reasoning=prompt,
        )
