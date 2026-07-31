from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import TradeSignal
from app.schemas.signals import SignalListResponse, TradeSignalResponse

router = APIRouter(prefix="/api/v1/signals", tags=["signals"])


@router.get("", response_model=SignalListResponse)
async def list_signals(
    status: str | None = Query(default=None),
    symbol: str | None = Query(default=None, min_length=1, max_length=16),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> SignalListResponse:
    query = select(TradeSignal).order_by(desc(TradeSignal.created_at)).limit(limit)
    if status:
        query = query.where(TradeSignal.status == status)
    if symbol:
        query = query.where(TradeSignal.symbol == symbol.strip().upper())
    rows = (await db.scalars(query)).all()
    items = [TradeSignalResponse.model_validate(row) for row in rows]
    return SignalListResponse(items=items, count=len(items))


@router.get("/{signal_id}", response_model=TradeSignalResponse)
async def get_signal(
    signal_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TradeSignalResponse:
    signal = await db.get(TradeSignal, signal_id)
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    return TradeSignalResponse.model_validate(signal)
