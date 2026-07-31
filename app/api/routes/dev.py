from datetime import datetime, timezone

from fastapi import APIRouter, Query
from redis.asyncio import Redis

from app.core.config import get_settings
from app.schemas.events import TradingViewWebhook

router = APIRouter(prefix="/api/v1/dev", tags=["development"])


@router.post("/seed")
async def seed(profile: str = Query(default="strong", pattern="^(weak|strong|bearish)$")) -> dict:
    settings = get_settings()
    profiles = {
        "weak": {
            "signal": "bullish_breakout",
            "close": "100",
            "indicators": {
                "rsi": 49,
                "ema_fast": 99,
                "ema_slow": 101,
                "ema_aligned": False,
                "vwap": 101,
                "above_vwap": False,
                "relative_volume": 0.85,
                "mtf_fast_trend": "neutral",
                "mtf_slow_trend": "bearish",
            },
        },
        "strong": {
            "signal": "bullish_breakout",
            "close": "190",
            "indicators": {
                "rsi": 61,
                "ema_fast": 188,
                "ema_slow": 184,
                "ema_aligned": True,
                "vwap": 187,
                "above_vwap": True,
                "relative_volume": 1.65,
                "mtf_fast_trend": "bullish",
                "mtf_slow_trend": "bullish",
            },
        },
        "bearish": {
            "signal": "bearish_breakdown",
            "close": "180",
            "indicators": {
                "rsi": 39,
                "ema_fast": 182,
                "ema_slow": 186,
                "ema_aligned": True,
                "vwap": 183,
                "above_vwap": False,
                "relative_volume": 1.55,
                "mtf_fast_trend": "bearish",
                "mtf_slow_trend": "bearish",
            },
        },
    }
    selected = profiles[profile]
    event = TradingViewWebhook(
        secret=settings.tradingview_webhook_secret,
        symbol="AAPL",
        timeframe="5",
        timestamp=datetime.now(timezone.utc),
        close=selected["close"],
        volume=1_000_000,
        signal=selected["signal"],
        strategy="ema_vwap_relative_volume_mtf",
        bar_confirmed=True,
        indicators=selected["indicators"],
    )
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        event_id = await redis.xadd("technical-signals", {"payload": event.model_dump_json()})
    finally:
        await redis.aclose()
    return {"seeded": True, "profile": profile, "event_id": event_id}
