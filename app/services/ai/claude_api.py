from __future__ import annotations

from anthropic import AsyncAnthropic

from app.services.ai.models import AIRecommendation


class ClaudeAPIClient:
    def __init__(
        self,
        api_key: str,
        model: str,
    ) -> None:
        self.client = AsyncAnthropic(api_key=api_key)
        self.model = model

    async def recommend(
        self,
        prompt: str,
    ) -> AIRecommendation:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1200,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
        )

        text = response.content[0].text

        return AIRecommendation(
            symbol="UNKNOWN",
            action="HOLD",
            confidence=50.0,
            risk="MEDIUM",
            entry="",
            stop_loss="",
            targets=(),
            position_size_pct=0.0,
            summary="Claude response received.",
            pros=(),
            cons=(),
            reasoning=text,
        )
