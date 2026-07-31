from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.brokers.factory import get_broker
from app.services.brokers.ibkr_historical import (
    IBKRConnectionError,
    IBKRDependencyError,
    IBKRRequestError,
)


router = APIRouter(
    prefix="/api/v1/historical",
    tags=["historical-market-data"],
)


class HistoricalBarResponse(BaseModel):
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


class HistoricalBarsResponse(BaseModel):
    symbol: str
    duration: str
    bar_size: str
    use_rth: bool
    count: int
    bars: list[HistoricalBarResponse]


@router.get(
    "/{symbol}",
    response_model=HistoricalBarsResponse,
)
async def get_historical_bars(
    symbol: str,
    duration: str = Query(
        default="1 D",
        min_length=3,
        max_length=16,
    ),
    bar_size: str = Query(
        default="5 mins",
        min_length=3,
        max_length=16,
    ),
    use_rth: bool = Query(default=True),
) -> HistoricalBarsResponse:
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=422,
            detail="Symbol must not be empty.",
        )

    broker = get_broker()

    try:
        bars = await broker.historical_bars(
            symbol=normalized_symbol,
            duration=duration,
            bar_size=bar_size,
            use_rth=use_rth,
        )
    except IBKRDependencyError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except IBKRConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc
    except IBKRRequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    response_bars = [
        HistoricalBarResponse(
            symbol=bar.symbol,
            timestamp=bar.timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )
        for bar in bars
    ]

    return HistoricalBarsResponse(
        symbol=normalized_symbol,
        duration=duration,
        bar_size=bar_size,
        use_rth=use_rth,
        count=len(response_bars),
        bars=response_bars,
    )
