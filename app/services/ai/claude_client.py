"""
AI recommendation service using Claude.
"""

import json
from typing import Any

import anthropic
from pydantic import BaseModel, Field

from app.core.config import get_settings, Settings
from app.core.errors import AIError


class TradeRecommendation(BaseModel):
    """Structured trade recommendation."""
    
    ticker: str
    action: str = Field(pattern="^(buy|sell|hold)$")
    quantity: int
    entry_price: float
    stop_loss: float
    target_price: float
    reasoning: str
    confidence: float = Field(ge=0, le=1)
    risk_reward_ratio: float
    technical_factors: list[str] = Field(default_factory=list)
    fundamental_factors: list[str] = Field(default_factory=list)


class ClaudeClient:
    """
    Client for interacting with Claude AI.
    
    Provides abstraction over Claude API calls for trade recommendations.
    """
    
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
    
    async def generate_recommendation(
        self,
        ticker: str,
        signal_data: dict[str, Any],
    ) -> TradeRecommendation:
        """
        Generate a trade recommendation using Claude.
        
        Args:
            ticker: Stock ticker symbol
            signal_data: Signal information including indicators
            
        Returns:
            Recommendation with reasoning and trade plan
            
        Raises:
            AIError: If Claude API call fails
        """
        if self.settings.ai_mode == "mock":
            return self._generate_mock_recommendation(ticker, signal_data)
        
        # Real Claude API call
        return await self._generate_claude_recommendation(ticker, signal_data)
    
    async def _generate_claude_recommendation(
        self,
        ticker: str,
        signal_data: dict[str, Any],
    ) -> TradeRecommendation:
        """
        Generate recommendation using Claude API.
        
        Args:
            ticker: Stock ticker symbol
            signal_data: Signal information
            
        Returns:
            Trade recommendation model
        """
        try:
            # Build prompt for Claude
            system_prompt = """You are a sophisticated trading assistant that analyzes technical indicators,
news sentiment, and market data to generate trade recommendations.

Return your response as a JSON object with the following structure:
{
    "ticker": string,
    "action": "buy" or "sell" or "hold",
    "quantity": integer,
    "entry_price": float,
    "stop_loss": float,
    "target_price": float,
    "reasoning": string,
    "confidence": float (0-1),
    "risk_reward_ratio": float,
    "technical_factors": list of strings,
    "fundamental_factors": list of strings
}

Be concise but thorough in your reasoning."""
            
            user_prompt = f"""Analyze the following trading signal for {ticker}:

Signal Type: {signal_data.get('signal_type', 'unknown')}
Confidence: {signal_data.get('confidence', 0)}
Technical Score: {signal_data.get('technical_score', 0)}

Indicators:
{json.dumps(signal_data.get('indicators', {}), indent=2)}

Current Price: {signal_data.get('current_price', 'N/A')}
Market Sentiment: {signal_data.get('sentiment', 'neutral')}

Please generate a trade recommendation."""
            
            response = self.client.messages.create(
                model=self.settings.ai_model,
                max_tokens=1000,
                system=[{"type": "text", "text": system_prompt}],
                messages=[{"role": "user", "content": user_prompt}],
            )
            
            # Parse response
            content = response.content[0].text
            
            # Extract JSON from response
            try:
                recommendation_data = json.loads(content)
            except json.JSONDecodeError:
                # Try to extract JSON from response
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    recommendation_data = json.loads(json_match.group())
                else:
                    raise AIError(f"Failed to parse Claude response: {content}")
            
            return TradeRecommendation(**recommendation_data)
        
        except anthropic.APIError as e:
            raise AIError(f"Claude API error: {e}")
        except Exception as e:
            raise AIError(f"Failed to generate recommendation: {e}")
    
    def _generate_mock_recommendation(
        self,
        ticker: str,
        signal_data: dict[str, Any],
    ) -> TradeRecommendation:
        """Generate mock recommendation for testing."""
        signal_type = signal_data.get('signal_type', 'neutral')
        
        if signal_type == 'bullish':
            action = 'buy'
            confidence = min(0.9, signal_data.get('confidence', 0.5) + 0.1)
        elif signal_type == 'bearish':
            action = 'sell'
            confidence = min(0.9, signal_data.get('confidence', 0.5) + 0.1)
        else:
            action = 'hold'
            confidence = signal_data.get('confidence', 0.3)
        
        current_price = signal_data.get('current_price', 175.0)
        stop_loss = current_price * (1 - 0.03)  # 3% stop loss
        target_price = current_price * (1 + 0.06)  # 6% target
        
        return TradeRecommendation(
            ticker=ticker,
            action=action,
            quantity=100,
            entry_price=current_price,
            stop_loss=stop_loss,
            target_price=target_price,
            reasoning=f"Based on {signal_type} technical indicators for {ticker}, "
                     f"with confidence score {confidence:.2f}.",
            confidence=confidence,
            risk_reward_ratio=2.0,
            technical_factors=list(signal_data.get('indicators', {}).keys()),
            fundamental_factors=[],
        )


class MockClaudeClient(ClaudeClient):
    """
    Mock Claude client for testing without API calls.
    
    Always returns mock recommendations with consistent format.
    """
    
    def __init__(self):
        super().__init__()
        self.settings.ai_mode = "mock"


class AIRecommendationService:
    """
    Service for generating AI recommendations.
    
    Coordinates between technical signals and Claude AI to generate
    trade recommendations with reasoning.
    """
    
    def __init__(self):
        self.client = ClaudeClient()
    
    async def generate_recommendation(
        self,
        ticker: str,
        signal_type: str,
        confidence: float,
        technical_score: float,
        indicators: dict[str, Any],
    ) -> TradeRecommendation:
        """
        Generate complete AI recommendation.
        
        Args:
            ticker: Stock ticker
            signal_type: bullish/bearish/neutral
            confidence: Signal confidence (0-1)
            technical_score: Technical analysis score (0-1)
            indicators: Current indicator values
            
        Returns:
            Complete recommendation with trade plan
        """
        signal_data = {
            "signal_type": signal_type,
            "confidence": confidence,
            "technical_score": technical_score,
            "indicators": indicators,
        }
        
        return await self.client.generate_recommendation(ticker, signal_data)
    
    async def generate_recommendation_with_news(
        self,
        ticker: str,
        signal_type: str,
        confidence: float,
        technical_score: float,
        indicators: dict[str, Any],
        news_data: list[dict[str, Any]] | None = None,
    ) -> TradeRecommendation:
        """
        Generate recommendation with news sentiment analysis.
        
        Args:
            ticker: Stock ticker
            signal_type: bullish/bearish/neutral
            confidence: Signal confidence (0-1)
            technical_score: Technical analysis score (0-1)
            indicators: Current indicator values
            news_data: Optional news articles with sentiment
            
        Returns:
            Complete recommendation including news impact
        """
        signal_data = {
            "signal_type": signal_type,
            "confidence": confidence,
            "technical_score": technical_score,
            "indicators": indicators,
        }
        
        if news_data:
            signal_data["news_sentiment"] = self._aggregate_news_sentiment(news_data)
        
        return await self.client.generate_recommendation(ticker, signal_data)
    
    def _aggregate_news_sentiment(self, news_data: list[dict[str, Any]]) -> str:
        """
        Aggregate sentiment from multiple news articles.
        
        Args:
            news_data: List of news articles
            
        Returns:
            Overall sentiment string
        """
        if not news_data:
            return "neutral"
        
        sentiments = [article.get("sentiment", "neutral") for article in news_data]
        
        # Count sentiments
        counts = {s: sentiments.count(s) for s in set(sentiments)}
        
        # Return most common sentiment
        return max(counts, key=counts.get)
