from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TradeSignalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    symbol: str
    direction: str
    strategy: str
    score: float
    status: str
    details: dict[str, Any]
    risk_approved: bool
    expires_at: datetime
    created_at: datetime


class SignalListResponse(BaseModel):
    items: list[TradeSignalResponse]
    count: int
