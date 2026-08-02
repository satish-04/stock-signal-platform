"""Signal API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.models import Signal
from app.db.session import get_session
from app.models.signals import (
    SignalCreate,
    SignalResponse,
    SignalUpdate,
)

router = APIRouter(prefix="/v1/signals", tags=["Signals"])


@router.get("/", response_model=list[SignalResponse])
async def get_signals(
    ticker: str | None = None,
    signal_type: str | None = None,
    status: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Get trading signals with optional filters.
    
    Args:
        ticker: Filter by ticker symbol
        signal_type: Filter by signal type (bullish/bearish/neutral)
        status: Filter by trade status
        limit: Maximum number of results
        db: Database session
        settings: Application settings
        
    Returns:
        List of trading signals
    """
    from sqlalchemy import select
    
    query = select(Signal)
    
    if ticker:
        query = query.where(Signal.ticker == ticker)
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    if status:
        query = query.where(Signal.status == status)
    
    query = query.order_by(Signal.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    signals = result.scalars().all()
    
    return [SignalResponse.model_validate(signal) for signal in signals]


@router.post("/", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreate,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Create a new trading signal.
    
    Args:
        signal_data: Signal data from input
        db: Database session
        settings: Application settings
        
    Returns:
        Created signal with ID
    """
    signal = Signal(
        ticker=signal_data.ticker,
        signal_type=signal_data.signal_type,
        confidence=float(signal_data.confidence),
        technical_score=float(signal_data.technical_score),
        reasons=signal_data.reasons,
        warnings=signal_data.warnings,
    )
    
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    
    return SignalResponse.model_validate(signal)


@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Get a specific signal by ID.
    
    Args:
        signal_id: Signal database ID
        db: Database session
        
    Returns:
        Signal details
    """
    from sqlalchemy import select
    
    query = select(Signal).where(Signal.id == signal_id)
    result = await db.execute(query)
    signal = result.scalar_one_or_none()
    
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    return SignalResponse.model_validate(signal)


@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: int,
    signal_update: SignalUpdate,
    db: AsyncSession = Depends(get_session),
):
    """
    Update a signal.
    
    Args:
        signal_id: Signal database ID
        signal_update: Signal update data
        
    Returns:
        Updated signal
    """
    from sqlalchemy import select
    
    query = select(Signal).where(Signal.id == signal_id)
    result = await db.execute(query)
    signal = result.scalar_one_or_none()
    
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    if signal_update.status is not None:
        signal.status = signal_update.status
    if signal_update.trade_id is not None:
        signal.trade_id = signal_update.trade_id
    
    await db.commit()
    await db.refresh(signal)
    
    return SignalResponse.model_validate(signal)


@router.delete("/{signal_id}", response_model=dict[str, str])
async def delete_signal(
    signal_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Delete a signal.
    
    Args:
        signal_id: Signal database ID
        
    Returns:
        Deletion confirmation
    """
    from sqlalchemy import delete, select
    
    # Check if signal exists
    query = select(Signal).where(Signal.id == signal_id)
    result = await db.execute(query)
    signal = result.scalar_one_or_none()
    
    if signal is None:
        raise HTTPException(status_code=404, detail="Signal not found")
    
    # Delete the signal
    delete_query = delete(Signal).where(Signal.id == signal_id)
    await db.execute(delete_query)
    await db.commit()
    
    return {"message": f"Signal {signal_id} deleted successfully"}
