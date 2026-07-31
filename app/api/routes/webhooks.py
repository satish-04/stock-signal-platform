from fastapi import APIRouter, HTTPException
from redis.asyncio import Redis
from app.core.config import get_settings
from app.schemas.events import TradingViewWebhook
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

@router.post("/tradingview", status_code=202)
async def tradingview(payload: TradingViewWebhook) -> dict:
    settings = get_settings()
    if payload.secret != settings.tradingview_webhook_secret:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    if not payload.bar_confirmed:
        raise HTTPException(status_code=422, detail="Only confirmed-bar signals are accepted")
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        event_id = await redis.xadd("technical-signals", {"payload": payload.model_dump_json()})
    finally:
        await redis.aclose()
    return {"accepted": True, "event_id": event_id}
