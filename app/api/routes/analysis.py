from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.brokers.factory import get_broker
from app.services.brokers.ibkr_historical import (
    IBKRConnectionError,
    IBKRDependencyError,
    IBKRRequestError,
)
from app.services.indicators.service import IndicatorService


router = APIRouter(
    prefix="/api/v1/analysis",
    tags=["technical-analysis"],
)


class TechnicalAnalysisResponse(BaseModel):
    symbol: str
    duration: str
    bar_size: str
    use_rth: bool
    ema_9: float | None
    ema_20: float | None
    ema_50: float | None
    ema_200: float | None
    sma_20: float | None
    rsi_14: float | None
    macd: float | None
    macd_signal: float | None
    macd_histogram: float | None
    atr_14: float | None
    vwap: float | None
    bollinger_upper: float | None
    bollinger_middle: float | None
    bollinger_lower: float | None


@router.get(
    "/{symbol}",
    response_model=TechnicalAnalysisResponse,
)
async def get_technical_analysis(
    symbol: str,
    duration: str = Query(
        default="5 D",
        min_length=3,
        max_length=16,
    ),
    bar_size: str = Query(
        default="5 mins",
        min_length=3,
        max_length=16,
    ),
    use_rth: bool = Query(default=True),
) -> TechnicalAnalysisResponse:
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=422,
            detail="Symbol must not be empty.",
        )

    service = IndicatorService(get_broker())

    try:
        result = await service.calculate_for_symbol(
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

    return TechnicalAnalysisResponse(
        symbol=normalized_symbol,
        duration=duration,
        bar_size=bar_size,
        use_rth=use_rth,
        ema_9=result.ema_9,
        ema_20=result.ema_20,
        ema_50=result.ema_50,
        ema_200=result.ema_200,
        sma_20=result.sma_20,
        rsi_14=result.rsi_14,
        macd=result.macd,
        macd_signal=result.macd_signal,
        macd_histogram=result.macd_histogram,
        atr_14=result.atr_14,
        vwap=result.vwap,
        bollinger_upper=result.bollinger_upper,
        bollinger_middle=result.bollinger_middle,
        bollinger_lower=result.bollinger_lower,
    )
