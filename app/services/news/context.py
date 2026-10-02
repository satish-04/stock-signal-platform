from datetime import datetime, timedelta, timezone

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import NewsEvent

RESEARCH_PROVIDERS = ("grok-x-research", "ai-trading-board")


async def recent_research_context(
    session: AsyncSession, symbol: str, limit: int = 5
) -> tuple[str | None, list[dict]]:
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    query = (
        select(NewsEvent)
        .where(
            NewsEvent.symbol == symbol.upper(),
            NewsEvent.provider.in_(RESEARCH_PROVIDERS),
            NewsEvent.published_at >= cutoff,
        )
        .order_by(desc(NewsEvent.published_at))
        .limit(limit)
    )
    rows = (await session.scalars(query)).all()
    if not rows:
        return None, []

    context = "\n\n".join(
        f"Source: {row.provider}; title: {row.headline}; published: {row.published_at.isoformat()}\n"
        f"{row.body or ''}"
        for row in rows
    )
    references = [
        {
            "id": str(row.id),
            "provider": row.provider,
            "source_id": row.source_id,
            "headline": row.headline,
            "published_at": row.published_at.isoformat(),
            "reviewed_by": (row.raw or {}).get("reviewed_by"),
        }
        for row in rows
    ]
    return context, references