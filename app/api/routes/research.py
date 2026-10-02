import hmac

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.models.entities import NewsEvent
from app.schemas.events import ResearchArtifactInput

router = APIRouter(prefix="/api/v1/research", tags=["research"])


@router.post("/artifacts", status_code=201)
async def import_artifact(
    artifact: ResearchArtifactInput,
    db: AsyncSession = Depends(get_db),
    x_webhook_secret: str = Header(default=""),
) -> dict:
    settings = get_settings()
    if not hmac.compare_digest(x_webhook_secret, settings.tradingview_webhook_secret):
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    event = NewsEvent(
        symbol=artifact.symbol,
        headline=artifact.headline,
        body=artifact.body,
        provider=artifact.provider,
        source_id=artifact.source_id,
        published_at=artifact.published_at,
        raw={"reviewed_by": artifact.reviewed_by, "human_reviewed": True},
    )
    try:
        db.add(event)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Research artifact already imported") from exc
    await db.refresh(event)
    return {
        "id": str(event.id),
        "symbol": event.symbol,
        "provider": event.provider,
        "source_id": event.source_id,
        "reviewed_by": artifact.reviewed_by,
    }


@router.get("/artifacts")
async def list_artifacts(
    symbol: str = Query(min_length=1, max_length=16),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from sqlalchemy import desc, select

    query = (
        select(NewsEvent)
        .where(
            NewsEvent.symbol == symbol.strip().upper(),
            NewsEvent.provider.in_(["grok-x-research", "ai-trading-board"]),
        )
        .order_by(desc(NewsEvent.published_at))
        .limit(limit)
    )
    rows = (await db.scalars(query)).all()
    return {
        "items": [
            {
                "id": str(row.id),
                "symbol": row.symbol,
                "provider": row.provider,
                "headline": row.headline,
                "body": row.body,
                "source_id": row.source_id,
                "published_at": row.published_at,
                "reviewed_by": (row.raw or {}).get("reviewed_by"),
            }
            for row in rows
        ],
        "count": len(rows),
    }