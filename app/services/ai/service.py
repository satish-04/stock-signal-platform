from __future__ import annotations

from app.services.ai.claude import MockClaudeClient
from app.services.indicators.service import IndicatorService
from app.services.signals.technical_engine import TechnicalSignalEngine


class AIRecommendationService:
    def __init__(self, broker) -> None:
        self.broker = broker
        self.indicators = IndicatorService(broker)
        self.client = MockClaudeClient()

    async def recommend(
        self,
        symbol: str,
        duration: str = "5 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ):
        indicator_result = await self.indicators.calculate_for_symbol(
            symbol=symbol,
            duration=duration,
            bar_size=bar_size,
            use_rth=use_rth,
        )

        technical_signal = TechnicalSignalEngine.evaluate(
            indicators=indicator_result,
            last_close=float(indicator_result.ema_9 or 0),
            relative_volume=1.5,
        )

        prompt = f"""
Symbol: {symbol}

Direction: {technical_signal.direction}
Confidence: {technical_signal.confidence}

Reasons:
{chr(10).join(technical_signal.reasons)}

Warnings:
{chr(10).join(technical_signal.warnings)}
"""

        return await self.client.recommend(prompt)
