"""
Signal models for database and API.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class SignalBase(BaseModel):
    """Base signal schema."""
    
    ticker: str = Field(..., min_length=1, max_length=10)
    signal_type: str = Field(..., pattern="^(bullish|bearish|neutral)$")
    confidence: Decimal = Field(..., ge=0, le=1)
    technical_score: Decimal = Field(..., ge=0, le=1)


class SignalCreate(SignalBase):
    """Request schema for creating a signal."""
    
    reasons: str | None = None
    warnings: str | None = None


class SignalResponse(SignalBase):
    """Response schema for signals."""
    
    id: int
    status: str = Field(default="pending", pattern="^(pending|approved|executed)$")
    ai_reasoning: str | None = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SignalUpdate(BaseModel):
    """Request schema for updating a signal."""
    
    status: str | None = Field(default=None, pattern="^(pending|approved|executed)$")
    trade_id: int | None = None


class TradeSignalCreate(BaseModel):
    """Request schema for creating a trade signal."""
    
    signal_id: int = Field(..., gt=0)
    trade_plan: str | None = None
    ai_recommendation: str | None = None
    status: str = Field(default="pending", pattern="^(pending|approved|rejected)$")


class TradeSignalResponse(TradeSignalCreate):
    """Response schema for trade signals."""
    
    id: int
    approved_at: datetime | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True
