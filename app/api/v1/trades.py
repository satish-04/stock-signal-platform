"""Trade execution API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.session import get_session
from app.models.trades import TradeCreate, TradeResponse

router = APIRouter(prefix="/v1/trades", tags=["Trades"])


@router.get("/", response_model=list[TradeResponse])
async def get_trades(
    status: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Get trade history with optional filters.
    
    Args:
        status: Filter by trade status
        limit: Maximum number of results
        db: Database session
        settings: Application settings
        
    Returns:
        List of trades
    """
    return []


@router.post("/", response_model=TradeResponse)
async def create_trade(
    trade_data: TradeCreate,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Create a new trade order.
    
    Args:
        trade_data: Trade order data
        db: Database session
        settings: Application settings
        
    Returns:
        Created trade with execution details
    """
    # Check safety switches
    if not settings.is_paper_mode:
        raise ValueError("Live trading is disabled")
    
    if not settings.enable_order_submission:
        raise ValueError("Order submission is disabled. Set ENABLE_ORDER_SUBMISSION=true")
    
    # Placeholder implementation
    return TradeResponse(
        id=1,
        ticker="AAPL",
        quantity=100,
        side="buy",
        order_type="market",
        status="executed",
        filled_qty=100,
        avg_fill_price=175.23,
    )


@router.post("/{trade_id}/execute", response_model=TradeResponse)
async def execute_trade(
    trade_id: int,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Execute a paper trade.
    
    Args:
        trade_id: Trade ID to execute
        db: Database session
        settings: Application settings
        
    Returns:
        Executed trade details
    """
    if not settings.is_paper_mode:
        raise ValueError("Not in paper mode")
    
    # Placeholder implementation
    return TradeResponse(
        id=trade_id,
        ticker="AAPL",
        quantity=100,
        side="buy",
        order_type="market",
        status="executed",
    )
