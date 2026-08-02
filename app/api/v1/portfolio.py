"""Portfolio API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.session import get_session

router = APIRouter(prefix="/v1/portfolio", tags=["Portfolio"])


@router.get("/summary")
async def get_portfolio_summary(
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Get portfolio summary with key metrics.
    
    Args:
        db: Database session
        settings: Application settings
        
    Returns:
        Portfolio summary including P&L, positions count, etc.
    """
    return {
        "total_equity": 100000.00,
        "day_pnl": 234.56,
        "total_return": 12.5,
        "positions_count": 3,
        "active_trades": 1,
        "cash_balance": 50000.00,
    }


@router.get("/positions", response_model=list[dict])
async def get_positions(
    status: str | None = None,
    db: AsyncSession = Depends(get_session),
):
    """
    Get all positions with optional status filter.
    
    Args:
        status: Filter by position status (open/closed)
        db: Database session
        
    Returns:
        List of positions
    """
    return []


@router.get("/positions/{position_id}")
async def get_position(
    position_id: int,
    db: AsyncSession = Depends(get_session),
):
    """
    Get detailed position information.
    
    Args:
        position_id: Position database ID
        db: Database session
        
    Returns:
        Position details including Greeks for options
    """
    return {
        "id": position_id,
        "ticker": "AAPL",
        "quantity": 100,
        "avg_cost": 172.45,
        "current_price": 175.23,
        "unrealized_pnl": 278.00,
        "pnl_percent": 1.61,
    }
