import pytest

from app.core.config import Settings
from app.services.background_jobs import (
    BackgroundAutomationDisabledError,
    BackgroundJobResult,
    BackgroundJobService,
    DuplicateBackgroundJobError,
    InMemoryBackgroundJobStore,
)


def build_settings(*, enabled: bool = True, retries: int = 2) -> Settings:
    return Settings(
        tradingview_webhook_secret="0123456789abcdef",
        background_automation_enabled=enabled,
        worker_max_retries=retries,
    )


@pytest.mark.asyncio
async def test_successful_job_lifecycle() -> None:
    service = BackgroundJobService(store=InMemoryBackgroundJobStore(), settings=build_settings())
    job = await service.create(job_type="WORKFLOW_RECONCILIATION", schedule_bucket="100")

    async def handler():
        return BackgroundJobResult(2, 2, 0, 0, ("done",))

    result = await service.run(job_id=job.job_id, handler=handler)
    assert result.status == "SUCCEEDED"
    assert result.attempt_count == 1
    assert result.result["processed"] == 2


@pytest.mark.asyncio
async def test_duplicate_job_is_blocked() -> None:
    service = BackgroundJobService(store=InMemoryBackgroundJobStore(), settings=build_settings())
    await service.create(job_type="EXIT_MONITORING", schedule_bucket="100")
    with pytest.raises(DuplicateBackgroundJobError):
        await service.create(job_type="EXIT_MONITORING", schedule_bucket="100")


@pytest.mark.asyncio
async def test_failed_job_is_retryable() -> None:
    service = BackgroundJobService(store=InMemoryBackgroundJobStore(), settings=build_settings())
    job = await service.create(job_type="POSITION_RECONCILIATION", schedule_bucket="100")

    async def handler():
        raise RuntimeError("temporary")

    with pytest.raises(RuntimeError):
        await service.run(job_id=job.job_id, handler=handler)
    persisted = await service.get(job.job_id)
    assert persisted.status == "FAILED"
    assert persisted.retryable is True
    assert persisted.attempt_count == 1


@pytest.mark.asyncio
async def test_dead_letter_after_attempt_limit() -> None:
    service = BackgroundJobService(
        store=InMemoryBackgroundJobStore(), settings=build_settings(retries=0)
    )
    job = await service.create(job_type="STALE_WORKFLOW_CLEANUP", schedule_bucket="100")

    async def handler():
        raise RuntimeError("permanent")

    result = await service.run(job_id=job.job_id, handler=handler)
    assert result.status == "DEAD_LETTER"
    assert result.retryable is False


@pytest.mark.asyncio
async def test_disabled_automation_blocks_run() -> None:
    service = BackgroundJobService(
        store=InMemoryBackgroundJobStore(), settings=build_settings(enabled=False)
    )
    job = await service.create(job_type="EXECUTION_RECONCILIATION", schedule_bucket="100")

    async def handler():
        raise AssertionError("handler must not run")

    with pytest.raises(BackgroundAutomationDisabledError):
        await service.run(job_id=job.job_id, handler=handler)
