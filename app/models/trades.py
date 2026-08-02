"""
Trade models for database and API.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TradeBase(BaseModel):
    """Base trade schema."""
    
    ticker: str = Field(..., min_length=1, max_length=10)
    quantity: int = Field(..., gt=0)
    side: str = Field(..., pattern="^(buy|sell)$")
    order_type: str = Field(default="market", pattern="^(market|limit)$")
    status: str = Field(default="pending", pattern="^(pending|executed|failed|cancelled)$")


class TradeCreate(TradeBase):
    """Request schema for creating a trade."""
    
    price: Decimal | None = None
    order_intent: str | None = None


class TradeResponse(TradeBase):
    """Response schema for trades."""
    
    id: int
    ib_order_id: str | None = None
    filled_qty: int | None = None
    avg_fill_price: Decimal | None = None
    filled_at: datetime | None = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TradeUpdate(BaseModel):
    """Request schema for updating a trade."""
    
    status: str | None = Field(default=None, pattern="^(pending|executed|failed|cancelled)$")
    ib_order_id: str | None = None
    filled_qty: int | None = None
    avg_fill_price: Decimal | None = None
