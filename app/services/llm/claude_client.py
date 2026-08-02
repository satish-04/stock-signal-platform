"""
LLM service abstraction.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.core.config import get_settings


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        max_tokens: int | None = None,
    ) -> dict[str, Any]:
        """
        Generate text from the LLM.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response from the LLM
        """
        pass


class ClaudeClient(LLMClient):
    """
    Client for Anthropic Claude API.
    
    Provides methods for generating trade recommendations,
    analyzing news, and reasoning about market conditions.
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    async def generate_trade_recommendation(
        self,
        ticker: str,
        signal_data: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Generate a trade recommendation using Claude.
        
        Args:
            ticker: Stock ticker
            signal_data: Technical signal data
            
        Returns:
            Recommendation with reasoning and trade plan
        """
        prompt = self._build_recommendation_prompt(ticker, signal_data)
        
        response = await self.generate(prompt, max_tokens=2000)
        
        return {
            "ticker": ticker,
            "action": response.get("action", "hold"),
            "quantity": response.get("quantity", 100),
            "entry_price": response.get("entry_price", 0),
            "stop_loss": response.get("stop_loss", 0),
            "target_price": response.get("target_price", 0),
            "reasoning": response.get("reasoning", ""),
            "confidence": response.get("confidence", 0.5),
        }
    
    async def analyze_news_catalyst(
        self,
        ticker: str,
        news_articles: list[dict[str, str]],
    ) -> dict[str, Any]:
        """
        Analyze news impact on a stock.
        
        Args:
            ticker: Stock ticker
            news_articles: List of news articles
            
        Returns:
            Analysis with sentiment and potential impact
        """
        prompt = self._build_news_analysis_prompt(ticker, news_articles)
        
        response = await self.generate(prompt, max_tokens=1500)
        
        return {
            "ticker": ticker,
            "sentiment": response.get("sentiment", "neutral"),
            "catalyst": response.get("catalyst", ""),
            "impact": response.get("impact", {}),
        }
    
    async def multi_agent_consensus(
        self,
        signals: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Get consensus from multiple AI agents.
        
        Args:
            signals: List of trade signals
            
        Returns:
            Consensus recommendation
        """
        prompt = self._build_consensus_prompt(signals)
        
        response = await self.generate(prompt, max_tokens=1000)
        
        return {
            "consensus": response.get("consensus", ""),
            "agreement_score": response.get("agreement_score", 0),
            "disagreements": response.get("disagreements", []),
        }
    
    def _build_recommendation_prompt(
        self,
        ticker: str,
        signal_data: dict[str, Any],
    ) -> str:
        """Build prompt for trade recommendation."""
        return f"""You are a stock trading AI assistant. Analyze the following technical signal and generate a trade recommendation.

Ticker: {ticker}
Signal Type: {signal_data.get('signal_type', 'unknown')}
Confidence: {signal_data.get('confidence', 0)}
Technical Score: {signal_data.get('technical_score', 0)}

Current Indicators:
{signal_data.get('indicators', {})}

Please provide a detailed trade recommendation including:
1. Action (buy/sell/hold)
2. Quantity
3. Entry price
4. Stop loss level
5. Target price
6. Reasoning for the recommendation

Return your response as a JSON object with these fields."""
    
    def _build_news_analysis_prompt(
        self,
        ticker: str,
        news_articles: list[dict[str, str]],
    ) -> str:
        """Build prompt for news analysis."""
        articles_text = "\n\n".join([
            f"Title: {a.get('title', '')}\nContent: {a.get('content', '')}"
            for a in news_articles
        ])
        
        return f"""Analyze the following news articles for {ticker} and determine the market sentiment.

{articles_text}

Please provide:
1. Overall sentiment (positive/negative/neutral)
2. Main catalyst for price movement
3. Potential short-term and long-term impact

Return your response as a JSON object."""
    
    def _build_consensus_prompt(
        self,
        signals: list[dict[str, Any]],
    ) -> str:
        """Build prompt for multi-agent consensus."""
        signals_text = "\n\n".join([
            f"Signal: {s.get('signal_type', '')}, Confidence: {s.get('confidence', 0)}"
            for s in signals
        ])
        
        return f"""You are a consensus AI that averages multiple trading signals.

Multiple AI agents have generated the following signals:

{signals_text}

Please provide:
1. Overall consensus (buy/sell/hold)
2. Agreement score (0-100)
3. Any significant disagreements

Return your response as a JSON object."""
    
    async def generate(
        self,
        prompt: str,
        max_tokens: int | None = 500,
    ) -> dict[str, Any]:
        """
        Generate text from Claude.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            Response dictionary
        """
        if self.settings.ai_mode == "mock":
            return self._generate_mock_response(prompt)
        
        # Real Claude API call
        raise NotImplementedError("Claude API integration not implemented")
    
    def _generate_mock_response(self, prompt: str) -> dict[str, Any]:
        """Generate mock response for testing."""
        return {
            "action": "buy",
            "quantity": 100,
            "entry_price": 175.0,
            "stop_loss": 168.75,
            "target_price": 183.75,
            "reasoning": "Based on bullish technical indicators for the given stock.",
            "confidence": 0.75,
        }


class MockClaudeClient(ClaudeClient):
    """
    Mock Claude client for testing.
    
    Always returns consistent mock responses.
    """
    
    def __init__(self):
        super().__init__()
        self.settings.ai_mode = "mock"
