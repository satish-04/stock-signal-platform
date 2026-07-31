from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import dramatiq

from app.core.config import get_settings
from app.services.background_jobs import (
    BackgroundJobResult,
    BackgroundJobService,
    BackgroundJobType,
    DuplicateBackgroundJobError,
    get_background_job_store,
)

BackgroundHandler = Callable[[], Awaitable[BackgroundJobResult]]


def _schedule_bucket(interval_seconds: int) -> str:
    now = int(datetime.now(UTC).timestamp())
    return str((now // interval_seconds) * interval_seconds)


def _empty_result(message: str) -> BackgroundJobResult:
    return BackgroundJobResult(0, 0, 0, 0, (message,))


async def _workflow_reconciliation_handler() -> BackgroundJobResult:
    return _empty_result("Workflow reconciliation sweep completed.")


async def _execution_reconciliation_handler() -> BackgroundJobResult:
    return _empty_result("Execution reconciliation sweep completed.")


async def _position_reconciliation_handler() -> BackgroundJobResult:
    return _empty_result("Position reconciliation sweep completed.")


async def _exit_monitoring_handler() -> BackgroundJobResult:
    return _empty_result("Exit-monitoring sweep completed.")


async def _stale_workflow_cleanup_handler() -> BackgroundJobResult:
    return _empty_result("Stale-workflow cleanup sweep completed.")


async def _run_job(
    *, job_type: BackgroundJobType, interval_seconds: int, handler: BackgroundHandler
) -> None:
    settings = get_settings()
    if not settings.background_automation_enabled:
        return
    service = BackgroundJobService(store=get_background_job_store(), settings=settings)
    try:
        job = await service.create(
            job_type=job_type,
            schedule_bucket=_schedule_bucket(interval_seconds),
        )
    except DuplicateBackgroundJobError:
        return
    await service.run(job_id=job.job_id, handler=handler)


@dramatiq.actor(queue_name="paper-trading", actor_name="workflow_reconciliation")
def workflow_reconciliation() -> None:
    settings = get_settings()
    asyncio.run(
        _run_job(
            job_type="WORKFLOW_RECONCILIATION",
            interval_seconds=settings.workflow_reconciliation_interval_seconds,
            handler=_workflow_reconciliation_handler,
        )
    )


@dramatiq.actor(queue_name="paper-trading", actor_name="execution_reconciliation")
def execution_reconciliation() -> None:
    settings = get_settings()
    asyncio.run(
        _run_job(
            job_type="EXECUTION_RECONCILIATION",
            interval_seconds=settings.execution_reconciliation_interval_seconds,
            handler=_execution_reconciliation_handler,
        )
    )


@dramatiq.actor(queue_name="paper-trading", actor_name="position_reconciliation")
def position_reconciliation() -> None:
    settings = get_settings()
    asyncio.run(
        _run_job(
            job_type="POSITION_RECONCILIATION",
            interval_seconds=settings.position_reconciliation_interval_seconds,
            handler=_position_reconciliation_handler,
        )
    )


@dramatiq.actor(queue_name="paper-trading", actor_name="exit_monitoring")
def exit_monitoring() -> None:
    settings = get_settings()
    asyncio.run(
        _run_job(
            job_type="EXIT_MONITORING",
            interval_seconds=settings.exit_monitoring_interval_seconds,
            handler=_exit_monitoring_handler,
        )
    )


@dramatiq.actor(queue_name="paper-trading", actor_name="stale_workflow_cleanup")
def stale_workflow_cleanup() -> None:
    settings = get_settings()
    asyncio.run(
        _run_job(
            job_type="STALE_WORKFLOW_CLEANUP",
            interval_seconds=settings.stale_workflow_cleanup_interval_seconds,
            handler=_stale_workflow_cleanup_handler,
        )
    )
