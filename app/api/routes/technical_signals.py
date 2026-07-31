from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.services.brokers.factory import get_broker
from app.services.indicators.service import IndicatorService
from app.services.signals.technical_engine import TechnicalSignalEngine

router = APIRouter(
    prefix="/api/v1/signals/technical",
    tags=["technical-signals"],
)


class TechnicalSignalResponse(BaseModel):
    symbol: str
    direction: str
    confidence: float
    trend_score: float
    momentum_score: float
    volatility_score: float
    volume_score: float
    reasons: list[str]
    warnings: list[str]


@router.get("/{symbol}", response_model=TechnicalSignalResponse)
async def technical_signal(
    symbol: str,
    duration: str = Query(default="5 D"),
    bar_size: str = Query(default="5 mins"),
    use_rth: bool = Query(default=True),
):
    broker = get_broker()
    service = IndicatorService(broker)

    try:
        indicators = await service.calculate_for_symbol(
            symbol=symbol.upper(),
            duration=duration,
            bar_size=bar_size,
            use_rth=use_rth,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    signal = TechnicalSignalEngine.evaluate(
        indicators=indicators,
        last_close=float(indicators.ema_9 or 0),
        relative_volume=1.5,
    )

    return TechnicalSignalResponse(
        symbol=symbol.upper(),
        direction=signal.direction,
        confidence=signal.confidence,
        trend_score=signal.trend_score,
        momentum_score=signal.momentum_score,
        volatility_score=signal.volatility_score,
        volume_score=signal.volume_score,
        reasons=list(signal.reasons),
        warnings=list(signal.warnings),
    )
