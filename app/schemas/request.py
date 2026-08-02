"""
Request schemas for API.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SignalCreate(BaseModel):
    """Request schema for creating a signal."""
    
    ticker: str = Field(..., min_length=1, max_length=10)
    signal_type: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    confidence: Decimal = Field(..., ge=0, le=1)
    technical_score: Decimal = Field(..., ge=0, le=1)


class TradeCreate(BaseModel):
    """Request schema for creating a trade."""
    
    ticker: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str | None = "market"  # market/limit
    price: Decimal | None = None


class OrderApproval(BaseModel):
    """Request schema for order approval."""
    
    trade_id: int = Field(..., gt=0)
    approved: bool
    notes: str | None = None


class WebhookNotification(BaseModel):
    """TradingView webhook notification."""
    
    ticker: str = Field(..., alias="ticker")
    signal: str = Field(..., alias="action")
    price: Decimal | None = None
    quantity: int | None = 100


class ScanRequest(BaseModel):
    """Market scan request."""
    
    tickers: list[str] = Field(..., min_length=1)
    timeframe: str | None = "1d"
    indicators: list[str] | None = None


class QuoteRequest(BaseModel):
    """Market quote request."""
    
    ticker: str = Field(..., min_length=1)
    include_greeks: bool | None = False
