"""
Technical analysis service.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.services.indicators.engine import IndicatorEngine


class TechnicalAnalysisService:
    """
    Service for comprehensive technical analysis.
    
    Provides technical indicators, pattern detection,
    and trend analysis.
    """
    
    def __init__(self):
        self.indicator_engine = IndicatorEngine()
    
    async def analyze_ticker(
        self,
        ticker: str,
        prices: pd.Series,
        volumes: pd.Series | None = None,
    ) -> dict:
        """
        Perform comprehensive technical analysis.
        
        Args:
            ticker: Stock ticker symbol
            prices: Price series
            volumes: Volume series (optional)
            
        Returns:
            Analysis results
        """
        # Calculate all indicators
        indicators = await self.indicator_engine.compute_all(prices, volumes)
        
        # Determine trend
        trend = self._determine_trend(prices, indicators)
        
        # Identify patterns
        patterns = self._identify_patterns(prices, volumes)
        
        return {
            "ticker": ticker,
            "timestamp": datetime.utcnow(),
            "indicators": indicators,
            "trend": trend,
            "patterns": patterns,
        }
    
    def _determine_trend(self, prices: pd.Series, indicators: dict) -> str:
        """
        Determine market trend.
        
        Args:
            prices: Price series
            indicators: Calculated indicators
            
        Returns:
            Trend string (uptrend/downtrend/neutral)
        """
        # Use multiple indicators to determine trend
        scores = []
        
        # EMA 50 vs EMA 200
        ema_50 = indicators.get("ema_50")
        ema_200 = indicators.get("ema_200")
        
        if ema_50 and ema_200:
            if ema_50 > ema_200:
                scores.append(1)  # Bullish
            else:
                scores.append(-1)  # Bearish
        
        # Current price vs moving averages
        close = prices.iloc[-1] if len(prices) > 0 else None
        
        for ma_name in ["ema_20", "sma_20"]:
            ma = indicators.get(ma_name)
            if ma and close:
                if close > ma:
                    scores.append(1)
                else:
                    scores.append(-1)
        
        # Average score
        if scores:
            avg_score = sum(scores) / len(scores)
            
            if avg_score > 0.5:
                return "uptrend"
            elif avg_score < -0.5:
                return "downtrend"
        
        return "neutral"
    
    def _identify_patterns(self, prices: pd.Series, volumes: pd.Series | None) -> list[str]:
        """
        Identify chart patterns.
        
        Args:
            prices: Price series
            volumes: Volume series (optional)
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Check for recent price action
        if len(prices) < 3:
            return patterns
        
        close = prices.iloc[-1]
        prev_close = prices.iloc[-2] if len(prices) > 1 else None
        prev_prev_close = prices.iloc[-3] if len(prices) > 2 else None
        
        # Bullish Engulfing pattern
        if prev_prev_close and prev_close:
            if prev_prev_close < prev_close and close > max(prev_close, prev_prev_close):
                patterns.append("bullish_engulfing")
        
        # Bearish Engulfing pattern
        if prev_prev_close and prev_close:
            if prev_prev_close > prev_close and close < min(prev_close, prev_prev_close):
                patterns.append("bearish_engulfing")
        
        # Double bottom pattern (simplified)
        if len(prices) >= 5:
            recent_lows = prices.tail(5).min()
            second_low = prices.iloc[-3] if len(prices) > 2 else None
            
            if second_low and abs(second_low - recent_lows) < 0.5:
                patterns.append("double_bottom")
        
        return patterns
    
    def calculate_support_resistance(self, prices: pd.Series) -> dict:
        """
        Calculate support and resistance levels.
        
        Args:
            prices: Price series
            
        Returns:
            Support and resistance levels
        """
        recent_high = prices.max()
        recent_low = prices.min()
        
        # Calculate pivot point
        close = prices.iloc[-1] if len(prices) > 0 else recent_low
        pivot = (recent_high + recent_low + close) / 3
        
        # Calculate support and resistance
        support1 = (pivot * 2) - recent_high
        resistance1 = (pivot * 2) - recent_low
        
        return {
            "support_1": float(support1),
            "pivot": float(pivot),
            "resistance_1": float(resistance1),
        }
