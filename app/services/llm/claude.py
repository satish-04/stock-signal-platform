import json
from anthropic import AsyncAnthropic
from app.core.config import get_settings

SYSTEM_PROMPT = """You are a financial-news classification component, not a trade executor.
Return only valid JSON. Separate facts from inference. Do not invent prices, option data, or events.
Classify direction, materiality, novelty, expected duration, confidence, risks, and invalidators.
Output keys: direction, sentiment_score, expected_impact, expected_duration, novelty_score,
confidence, key_facts, known_risks, invalidating_conditions, recommended_bias.
Allowed direction: bullish, bearish, neutral. Allowed recommended_bias: bullish_defined_risk,
bearish_defined_risk, volatility, no_trade."""

class ClaudeNewsAnalyzer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = AsyncAnthropic(api_key=self.settings.anthropic_api_key) if self.settings.anthropic_api_key else None

    async def analyze(self, symbol: str, headline: str, body: str | None) -> dict:
        if not self.client:
            return {
                "direction": "neutral", "sentiment_score": 0.0, "expected_impact": "low",
                "expected_duration": "unknown", "novelty_score": 0.0, "confidence": 0.0,
                "key_facts": [headline], "known_risks": ["Claude API not configured"],
                "invalidating_conditions": [], "recommended_bias": "no_trade",
            }
        response = await self.client.messages.create(
            model=self.settings.claude_model,
            max_tokens=900,
            temperature=0,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"Symbol: {symbol}\nHeadline: {headline}\nBody: {body or ''}"}],
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", "") == "text")
        return json.loads(text)
