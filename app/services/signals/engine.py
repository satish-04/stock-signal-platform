"""
Technical signal engine.
"""

from datetime import datetime
from decimal import Decimal

import pandas as pd

from app.core.constants import (
    CONFIDENCE_HIGH,
    CONFIDENCE_LOW,
    CONFIDENCE_MEDIUM,
)
from app.services.indicators.engine import IndicatorEngine


class TechnicalSignalEngine:
    """
    Engine for generating technical trading signals.
    
    Combines multiple indicators to generate
    bullish/bearish/neutral signals with confidence scores.
    """
    
    def __init__(self):
        self.indicator_engine = IndicatorEngine()
    
    async def generate_signal(
        self,
        ticker: str,
        prices: pd.Series,
        volumes: pd.Series | None = None,
    ) -> dict:
        """
        Generate a technical signal for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            prices: Price series (close prices)
            volumes: Optional volume series
            
        Returns:
            Signal dictionary with type, confidence, and details
        """
        # Calculate all indicators
        indicators = await self.indicator_engine.compute_all(prices, volumes)
        
        # Generate signal based on technical factors
        signal_type = self._determine_signal_type(indicators)
        confidence = self._calculate_confidence(indicators, signal_type)
        
        # Generate reasons for the signal
        reasons = self._generate_reasons(indicators, signal_type)
        
        # Generate warnings if needed
        warnings = self._generate_warnings(indicators)
        
        return {
            "ticker": ticker,
            "signal_type": signal_type,
            "confidence": confidence,
            "technical_score": self._calculate_technical_score(indicators),
            "indicators": indicators,
            "reasons": reasons,
            "warnings": warnings,
            "timestamp": datetime.utcnow(),
        }
    
    def _determine_signal_type(self, indicators: dict) -> str:
        """
        Determine bullish/bearish/neutral signal.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Signal type string
        """
        # Simple scoring system
        score = 0
        
        # EMA trends
        if indicators.get("ema_20") and indicators.get("close"):
            if indicators["ema_20"] < indicators["close"]:
                score += 1
            else:
                score -= 1
        
        # RSI
        rsi = indicators.get("rsi")
        if rsi:
            if rsi < 30:
                score += 2  # Oversold, potential bullish
            elif rsi > 70:
                score -= 2  # Overbought, potential bearish
            elif rsi < 50:
                score -= 1
            else:
                score += 1
        
        # MACD
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        
        if macd and macd_signal:
            if macd > macd_signal:
                score += 1
            else:
                score -= 1
        
        # Volatility (ATR)
        atr = indicators.get("atr")
        
        if atr:
            score += 0.5  # Some volatility is good for trading
        
        # Determine signal type
        if score >= 2:
            return "bullish"
        elif score <= -2:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_confidence(self, indicators: dict, signal_type: str) -> float:
        """
        Calculate confidence score for the signal.
        
        Args:
            indicators: Dictionary of indicator values
            signal_type: Generated signal type
            
        Returns:
            Confidence score (0-1)
        """
        confidence = 0.5  # Base confidence
        
        # Increase confidence with more indicators agreeing
        indicator_count = sum(1 for v in indicators.values() if v is not None)
        
        # RSI agreement
        rsi = indicators.get("rsi")
        if rsi:
            if signal_type == "bullish" and rsi < 40:
                confidence += 0.15
            elif signal_type == "bearish" and rsi > 60:
                confidence += 0.15
        
        # MACD agreement
        macd = indicators.get("macd")
        if macd:
            if (signal_type == "bullish" and macd > 0) or \
               (signal_type == "bearish" and macd < 0):
                confidence += 0.15
        
        # Volume confirmation
        if indicators.get("volume") and signal_type != "neutral":
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def _calculate_technical_score(self, indicators: dict) -> float:
        """
        Calculate overall technical score.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Technical score (0-1)
        """
        # Weighted average of key indicators
        scores = []
        
        rsi = indicators.get("rsi")
        if rsi is not None:
            # Normalize RSI to 0-1 scale
            scores.append((rsi - 30) / 70)
        
        macd = indicators.get("macd")
        if macd is not None:
            # Normalize MACD (simplified)
            scores.append(0.5)  # Would need actual distribution
        
        # Average all scores
        if scores:
            return sum(scores) / len(scores)
        else:
            return 0.5
    
    def _generate_reasons(self, indicators: dict, signal_type: str) -> list[str]:
        """
        Generate human-readable reasons for the signal.
        
        Args:
            indicators: Dictionary of indicator values
            signal_type: Generated signal type
            
        Returns:
            List of reasons
        """
        reasons = []
        
        if signal_type == "bullish":
            # Bullish reasons
            rsi = indicators.get("rsi")
            if rsi and rsi < 40:
                reasons.append("RSI indicates oversold conditions")
            
            ema_20 = indicators.get("ema_20")
            close = indicators.get("close")
            if ema_20 and close and close > ema_20:
                reasons.append("Price above 20-period EMA")
            
            macd = indicators.get("macd")
            if macd and macd > 0:
                reasons.append("MACD is positive and above signal line")
            
        elif signal_type == "bearish":
            # Bearish reasons
            rsi = indicators.get("rsi")
            if rsi and rsi > 70:
                reasons.append("RSI indicates overbought conditions")
            
            ema_20 = indicators.get("ema_20")
            close = indicators.get("close")
            if ema_20 and close and close < ema_20:
                reasons.append("Price below 20-period EMA")
            
            macd = indicators.get("macd")
            if macd and macd < 0:
                reasons.append("MACD is negative and below signal line")
        
        else:
            reasons.append("Mixed technical signals")
        
        return reasons
    
    def _generate_warnings(self, indicators: dict) -> list[str]:
        """
        Generate warnings about potential issues.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            List of warnings
        """
        warnings = []
        
        # Low volume warning
        volume = indicators.get("volume")
        if volume and volume < 100000:
            warnings.append("Low trading volume")
        
        # High volatility warning
        atr = indicators.get("atr")
        if atr and atr > 5.0:
            warnings.append("High volatility detected")
        
        return warnings
