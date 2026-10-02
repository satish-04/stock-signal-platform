import asyncio
from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.entities import OptionsScan
from app.schemas.scanner import OptionsScanRequest
from app.services.scanner import service as scanner

router = APIRouter(prefix="/api/v1/scanner", tags=["scanner"])

# Serializes scan starts so two requests cannot both find "no scan running".
_start_lock = asyncio.Lock()


def _view(scan: OptionsScan) -> dict:
    return {
        "id": str(scan.id),
        "status": scan.status,
        "expiry": scan.expiry.isoformat(),
        "universe_size": scan.universe_size,
        "scanned": scan.scanned,
        "skipped": scan.skipped,
        "started_at": scan.started_at,
        "completed_at": scan.completed_at,
        "error": scan.error,
        "progress": scanner.progress(scan.id),
        "result": scan.result,
    }


async def _reconcile(scan: OptionsScan | None, db: AsyncSession) -> OptionsScan | None:
    """Fail a scan that is marked running but is no longer running in this process."""
    if scan and scan.status == "running" and not scanner.is_active(scan.id):
        scan.status = "failed"
        scan.error = "Scan was interrupted before it finished"
        scan.completed_at = datetime.now(timezone.utc)
        await db.commit()
    return scan


async def _latest(db: AsyncSession) -> OptionsScan | None:
    query = select(OptionsScan).order_by(desc(OptionsScan.started_at)).limit(1)
    return await _reconcile((await db.scalars(query)).first(), db)


@router.post("/options", status_code=202)
async def start_options_scan(
    request: OptionsScanRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Start a scan, or return the one already running."""
    request = request or OptionsScanRequest()
    expiry = request.expiry or scanner.default_expiry()
    if expiry < scanner.market_today():
        raise HTTPException(status_code=422, detail="Expiry must be today or later")

    async with _start_lock:
        latest = await _latest(db)
        if latest and latest.status == "running":
            return {"scan": _view(latest), "started": False}
        scan = OptionsScan(status="running", expiry=expiry)
        db.add(scan)
        await db.commit()
        await db.refresh(scan)
        scanner.start_scan(scan.id, expiry, request.symbols)
    return {"scan": _view(scan), "started": True}


@router.get("/options/latest")
async def latest_options_scan(db: AsyncSession = Depends(get_db)) -> dict:
    """Return the newest scan, plus the last completed one when the newest has no results."""
    scan = await _latest(db)
    last_completed = None
    if scan and scan.status != "completed":
        query = (
            select(OptionsScan)
            .where(OptionsScan.status == "completed")
            .order_by(desc(OptionsScan.started_at))
            .limit(1)
        )
        last_completed = (await db.scalars(query)).first()
    return {
        "scan": _view(scan) if scan else None,
        "last_completed": _view(last_completed) if last_completed else None,
    }


@router.get("/options/{scan_id}")
async def get_options_scan(scan_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    scan = await _reconcile(await db.get(OptionsScan, scan_id), db)
    if scan is None:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {"scan": _view(scan)}
