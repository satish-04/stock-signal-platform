from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from redis.asyncio import Redis

from app.core.config import get_settings
from app.services.background_jobs import (
    BackgroundJob,
    BackgroundJobNotFoundError,
    BackgroundJobService,
    BackgroundJobStatus,
    BackgroundJobType,
    get_background_job_store,
)

router = APIRouter(prefix="/api/v1/background-jobs", tags=["background-jobs"])


class BackgroundJobResponse(BaseModel):
    job_id: str
    idempotency_key: str
    job_type: BackgroundJobType
    status: BackgroundJobStatus
    scope_id: str | None
    account_id: str | None
    attempt_count: int
    max_attempts: int
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    result: dict | None
    error_type: str | None
    error_message: str | None
    retryable: bool


class WorkerHealthResponse(BaseModel):
    status: str
    automation_enabled: bool
    redis_connected: bool
    queue_name: str
    safety: dict[str, bool | str]


@router.get("/health", response_model=WorkerHealthResponse)
async def worker_health() -> WorkerHealthResponse:
    settings = get_settings()
    redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        connected = bool(await redis.ping())
    except Exception:  # noqa: BLE001 - health must degrade for any Redis failure
        connected = False
    finally:
        await redis.aclose()
    return WorkerHealthResponse(
        status="ok" if connected else "degraded",
        automation_enabled=settings.background_automation_enabled,
        redis_connected=connected,
        queue_name=settings.worker_queue_name,
        safety={
            "trading_mode": settings.trading_mode,
            "manual_approval_required": settings.paper_workflow_require_manual_approval,
            "auto_submit": settings.paper_workflow_auto_submit,
            "order_submission_enabled": settings.enable_order_submission,
            "live_trading_enabled": settings.enable_live_trading,
        },
    )


@router.get("/{job_id}", response_model=BackgroundJobResponse)
async def get_background_job(job_id: str) -> BackgroundJob:
    service = BackgroundJobService(store=get_background_job_store())
    try:
        return await service.get(job_id)
    except BackgroundJobNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
