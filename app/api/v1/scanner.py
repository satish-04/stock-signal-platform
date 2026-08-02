"""Market scanner API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/v1/scanner", tags=["Scanner"])


@router.get("/")
async def scan_market():
    """
    Scan market for trading signals.
    
    Returns:
        List of scanner results
    """
    return [
        {"ticker": "AAPL", "price": 175.23, "change": "+1.2%", "volume": "45M", "signal": "bullish"},
        {"ticker": "NVDA", "price": 923.45, "change": "-0.8%", "volume": "32M", "signal": "bearish"},
        {"ticker": "TSLA", "price": 245.67, "change": "+2.1%", "volume": "28M", "signal": "bullish"},
        {"ticker": "META", "price": 489.32, "change": "+0.5%", "volume": "18M", "signal": "neutral"},
        {"ticker": "AMD", "price": 167.89, "change": "-1.5%", "volume": "35M", "signal": "bearish"},
    ]
