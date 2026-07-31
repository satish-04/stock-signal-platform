from datetime import datetime, timezone
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field, field_validator

class TradingViewWebhook(BaseModel):
    secret: str
    symbol: str = Field(min_length=1, max_length=16)
    exchange: str | None = None
    timeframe: str = "5"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    close: Decimal = Field(gt=0)
    volume: Decimal = Field(ge=0, default=0)
    signal: str
    strategy: str = "technical"
    bar_confirmed: bool = True
    indicators: dict[str, float | int | str | bool] = Field(default_factory=dict)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()

class NewsInput(BaseModel):
    symbol: str
    headline: str
    body: str | None = None
    provider: str = "manual"
    source_id: str
    published_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SignalView(BaseModel):
    symbol: str
    direction: Literal["bullish", "bearish", "neutral"]
    strategy: str
    score: float
    status: str
    details: dict
