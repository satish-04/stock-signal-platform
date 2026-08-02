"""Option chain API endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.session import get_session

router = APIRouter(prefix="/v1/options", tags=["Options"])


@router.get("/{ticker}", response_model=dict)
async def get_option_chain(
    ticker: str,
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Get option chain for a ticker.
    
    Args:
        ticker: Stock ticker
        db: Database session
        settings: Application settings
        
    Returns:
        Option chain data
    """
    # Placeholder implementation - return mock data with required fields
    now = datetime.now()
    
    # Return a simple dict that matches the response model
    return {
        "ticker": ticker,
        "expiry_date": now.strftime("%Y-%m-%dT%H:%M:%S"),
        "strike_price": 175.0,
        "right": "C",
        "conid": 123456789,
        "underlying_price": 175.0,
        "id": 1,
        "bid": 0.0,
        "ask": 0.0,
        "volume": 0,
        "open_interest": 0,
        "iv": 0.0,
        "delta": 0.0,
        "gamma": 0.0,
        "theta": 0.0,
        "vega": 0.0,
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@router.get("/", response_model=list[dict])
async def get_option_chains(
    ticker_list: list[str],
    db: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
):
    """
    Get option chains for a list of tickers.
    
    Args:
        ticker_list: List of stock tickers
        db: Database session
        settings: Application settings
        
    Returns:
        List of option chain data
    """
    return []
