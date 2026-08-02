"""
Pydantic models for indicators.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class IndicatorValue(BaseModel):
    """Single indicator value."""
    
    name: str
    value: Decimal
    timestamp: datetime


class TechnicalIndicators(BaseModel):
    """All technical indicators for a symbol."""
    
    ticker: str
    timestamp: datetime
    
    # Moving Averages
    ema_9: Decimal | None = None
    ema_20: Decimal | None = None
    ema_50: Decimal | None = None
    ema_200: Decimal | None = None
    sma_20: Decimal | None = None
    
    # Momentum
    rsi_14: Decimal | None = None
    macd: Decimal | None = None
    macd_signal: Decimal | None = None
    macd_histogram: Decimal | None = None
    
    # Volatility
    atr_14: Decimal | None = None
    bollinger_upper: Decimal | None = None
    bollinger_middle: Decimal | None = None
    bollinger_lower: Decimal | None = None
    
    # Volume
    vwap: Decimal | None = None
    volume: int | None = None


class SignalScore(BaseModel):
    """Signal scoring components."""
    
    trend_score: Decimal
    momentum_score: Decimal
    volatility_score: Decimal
    volume_score: Decimal
    
    @property
    def total_score(self) -> Decimal:
        """Calculate weighted total score."""
        return (
            self.trend_score * 0.35
            + self.momentum_score * 0.25
            + self.volatility_score * 0.20
            + self.volume_score * 0.20
        )


class TechnicalSignal(BaseModel):
    """Complete technical signal."""
    
    ticker: str
    signal_type: str  # bullish/bearish/neutral
    confidence: Decimal
    technical_score: Decimal
    signal_score: SignalScore
    reasons: list[str]
    warnings: list[str] | None = None


class OptionChain(BaseModel):
    """Option chain contract details."""
    
    expiry_date: str
    strike_price: Decimal
    right: str  # C/P
    conid: int
    
    # Market data
    bid: Decimal = Decimal("0.00")
    ask: Decimal = Decimal("0.00")
    volume: int = 0
    open_interest: int = 0
    
    # Greeks
    iv: Decimal = Decimal("0.0000")
    delta: Decimal = Decimal("0.0000")
    gamma: Decimal = Decimal("0.0000")
    theta: Decimal = Decimal("0.0000")
    vega: Decimal = Decimal("0.0000")
    
    underlying_price: Decimal


class OptionChainResponse(BaseModel):
    """Complete option chain response."""
    
    ticker: str
    underlying_price: Decimal
    contracts: list[dict]


class HistoricalBar(BaseModel):
    """Historical price bar."""
    
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int | None = None
