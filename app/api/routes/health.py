from fastapi import APIRouter
from app.core.config import get_settings
router = APIRouter()
@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {"status": "ok", "environment": s.app_env, "trading_mode": s.trading_mode,
            "market_data_mode": s.market_data_mode, "orders_enabled": s.enable_order_submission}
