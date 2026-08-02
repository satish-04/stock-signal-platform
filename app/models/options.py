"""
Option models for database and API.
"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class OptionChainBase(BaseModel):
    """Base option chain schema."""
    
    ticker: str = Field(..., min_length=1, max_length=10)
    expiry_date: datetime
    strike_price: Decimal = Field(..., gt=0)
    right: str = Field(..., pattern="^[CP]$")
    conid: int = Field(..., gt=0)
    underlying_price: Decimal = Field(..., gt=0)


class OptionChainCreate(OptionChainBase):
    """Request schema for creating an option chain."""
    
    bid: Decimal = Field(default="0.00", ge=0)
    ask: Decimal = Field(default="0.00", ge=0)
    volume: int = Field(default=0)
    open_interest: int = Field(default=0)
    iv: Decimal = Field(default="0.0000", ge=0)
    delta: Decimal = Field(default="0.0000")
    gamma: Decimal = Field(default="0.0000")
    theta: Decimal = Field(default="0.0000")
    vega: Decimal = Field(default="0.0000")


class OptionChainResponse(OptionChainBase):
    """Response schema for option chains."""
    
    id: int
    bid: Decimal = Field(default="0.00")
    ask: Decimal = Field(default="0.00")
    volume: int = Field(default=0)
    open_interest: int = Field(default=0)
    iv: Decimal = Field(default="0.0000")
    delta: Decimal = Field(default="0.0000")
    gamma: Decimal = Field(default="0.0000")
    theta: Decimal = Field(default="0.0000")
    vega: Decimal = Field(default="0.0000")
    created_at: datetime
    
    class Config:
        from_attributes = True


class OptionQuote(BaseModel):
    """Response schema for option quotes."""
    
    ticker: str
    strike_price: Decimal
    expiry_date: datetime
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


class OptionChainListResponse(BaseModel):
    """Response schema for option chain lists."""
    
    ticker: str
    chains: list[OptionChainResponse] = Field(default_factory=list)
