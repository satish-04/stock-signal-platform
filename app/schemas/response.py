"""
Response schemas for API.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SignalResponse(BaseModel):
    """Response schema for signals."""
    
    id: int
    ticker: str
    signal_type: str  # bullish/bearish/neutral
    confidence: Decimal
    technical_score: Decimal
    status: str  # pending/approved/executed
    created_at: datetime


class TradeResponse(BaseModel):
    """Response schema for trades."""
    
    id: int
    ticker: str
    quantity: int
    side: str  # buy/sell
    order_type: str
    status: str  # pending/executed/failed
    filled_qty: int | None = None
    avg_fill_price: Decimal | None = None


class PositionResponse(BaseModel):
    """Response schema for positions."""
    
    id: int
    ticker: str
    quantity: int
    avg_cost: Decimal
    current_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    pnl_percent: Decimal | None = None


class PortfolioSummary(BaseModel):
    """Response schema for portfolio summary."""
    
    total_equity: Decimal
    day_pnl: Decimal
    total_return: Decimal
    positions_count: int
    active_trades: int
    cash_balance: Decimal


class QuoteResponse(BaseModel):
    """Response schema for market quotes."""
    
    ticker: str
    bid: Decimal | None = None
    ask: Decimal | None = None
    last_price: Decimal | None = None
    volume: int | None = None


class OptionQuote(BaseModel):
    """Response schema for option quotes."""
    
    ticker: str
    strike_price: Decimal
    expiry_date: str
    right: str  # C/P
    bid: Decimal | None = None
    ask: Decimal | None = None
    volume: int | None = None
    open_interest: int | None = None
    iv: Decimal | None = None
    delta: Decimal | None = None
    gamma: Decimal | None = None
    theta: Decimal | None = None
    vega: Decimal | None = None


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    database: str | None = None
    redis: str | None = None
    broker: str | None = None


class ScanResponse(BaseModel):
    """Market scan response."""
    
    results: list[dict]
    total_count: int
    timestamp: datetime
