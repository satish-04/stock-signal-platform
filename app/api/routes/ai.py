from __future__ import annotations

from fastapi import APIRouter

from app.services.ai.service import AIRecommendationService
from app.services.brokers.factory import get_broker

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"],
)


@router.get("/recommendation/{symbol}")
async def recommendation(symbol: str):
    service = AIRecommendationService(get_broker())
    result = await service.recommend(symbol.upper())

    return {
        "symbol": result.symbol,
        "action": result.action,
        "confidence": result.confidence,
        "risk": result.risk,
        "entry": result.entry,
        "stop_loss": result.stop_loss,
        "targets": list(result.targets),
        "position_size_pct": result.position_size_pct,
        "summary": result.summary,
        "pros": list(result.pros),
        "cons": list(result.cons),
        "reasoning": result.reasoning,
    }
