from __future__ import annotations

import hashlib
from collections.abc import Awaitable, Callable
from dataclasses import replace
from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.services.background_jobs.models import (
    BackgroundJob,
    BackgroundJobResult,
    BackgroundJobType,
)
from app.services.background_jobs.store import BackgroundJobNotFoundError, BackgroundJobStore

BackgroundJobHandler = Callable[[], Awaitable[BackgroundJobResult]]


class BackgroundAutomationDisabledError(PermissionError):
    """Raised when background automation is disabled."""


class BackgroundJobService:
    def __init__(self, *, store: BackgroundJobStore, settings: Settings | None = None) -> None:
        self.store = store
        self.settings = settings or get_settings()

    @staticmethod
    def _idempotency_key(
        *,
        job_type: BackgroundJobType,
        scope_id: str | None,
        account_id: str | None,
        schedule_bucket: str,
    ) -> str:
        payload = "|".join([job_type, scope_id or "", account_id or "", schedule_bucket])
        return hashlib.sha256(payload.encode()).hexdigest()

    @staticmethod
    def _job_id(idempotency_key: str) -> str:
        return f"job_{idempotency_key[:24]}"

    async def create(
        self,
        *,
        job_type: BackgroundJobType,
        schedule_bucket: str,
        scope_id: str | None = None,
        account_id: str | None = None,
    ) -> BackgroundJob:
        idempotency_key = self._idempotency_key(
            job_type=job_type,
            scope_id=scope_id,
            account_id=account_id,
            schedule_bucket=schedule_bucket,
        )
        job_id = self._job_id(idempotency_key)
        await self.store.reserve(idempotency_key, job_id)
        now = datetime.now(UTC)
        job = BackgroundJob(
            job_id=job_id,
            idempotency_key=idempotency_key,
            job_type=job_type,
            status="QUEUED",
            scope_id=scope_id,
            account_id=account_id,
            attempt_count=0,
            max_attempts=self.settings.worker_max_retries + 1,
            queued_at=now,
            started_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
            result=None,
            error_type=None,
            error_message=None,
            retryable=True,
        )
        try:
            await self.store.save(job)
        except Exception:
            await self.store.release(idempotency_key)
            raise
        return job

    async def get(self, job_id: str) -> BackgroundJob:
        job = await self.store.get(job_id.strip())
        if job is None:
            raise BackgroundJobNotFoundError(f"Background job {job_id!r} was not found.")
        return job

    async def run(self, *, job_id: str, handler: BackgroundJobHandler) -> BackgroundJob:
        if not self.settings.background_automation_enabled:
            raise BackgroundAutomationDisabledError("Background automation is disabled.")
        job = await self.get(job_id)
        if job.status in {"SUCCEEDED", "SKIPPED", "DEAD_LETTER"}:
            return job
        now = datetime.now(UTC)
        running = replace(
            job,
            status="RUNNING",
            attempt_count=job.attempt_count + 1,
            started_at=now,
            updated_at=now,
            error_type=None,
            error_message=None,
        )
        await self.store.save(running)
        try:
            result = await handler()
        except Exception as exc:
            completed_at = datetime.now(UTC)
            exhausted = running.attempt_count >= running.max_attempts
            failed = replace(
                running,
                status="DEAD_LETTER" if exhausted else "FAILED",
                completed_at=completed_at,
                updated_at=completed_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
                retryable=not exhausted,
            )
            await self.store.save(failed)
            if not exhausted:
                raise
            return failed
        completed_at = datetime.now(UTC)
        succeeded = replace(
            running,
            status="SUCCEEDED",
            completed_at=completed_at,
            updated_at=completed_at,
            result={
                "processed": result.processed,
                "succeeded": result.succeeded,
                "failed": result.failed,
                "skipped": result.skipped,
                "details": list(result.details),
            },
            retryable=False,
        )
        await self.store.save(succeeded)
        return succeeded

    async def skip(self, *, job_id: str, reason: str) -> BackgroundJob:
        job = await self.get(job_id)
        now = datetime.now(UTC)
        skipped = replace(
            job,
            status="SKIPPED",
            completed_at=now,
            updated_at=now,
            result={
                "processed": 0,
                "succeeded": 0,
                "failed": 0,
                "skipped": 1,
                "details": [reason],
            },
            retryable=False,
        )
        await self.store.save(skipped)
        return skipped
