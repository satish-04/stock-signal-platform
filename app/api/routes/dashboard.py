from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import TradeSignal

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])

@router.get("/summary")
async def summary(db: AsyncSession = Depends(get_db)) -> dict:
    grouped = dict((await db.execute(select(TradeSignal.status, func.count()).group_by(TradeSignal.status))).all())
    latest = (await db.scalars(select(TradeSignal).order_by(TradeSignal.created_at.desc()).limit(1))).first()
    return {
        "total_signals": sum(grouped.values()),
        "actionable": grouped.get("actionable", 0),
        "review": grouped.get("review", 0),
        "rejected": grouped.get("rejected", 0),
        "latest_score": float(latest.score) if latest else None,
        "latest_symbol": latest.symbol if latest else None,
        "services": {"api": "healthy", "postgres": "connected", "worker": "external", "orders": "disabled"},
    }
