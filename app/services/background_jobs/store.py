from __future__ import annotations

import asyncio
import json
from datetime import datetime
from typing import Any, Protocol

from redis.asyncio import Redis

from app.services.background_jobs.models import BackgroundJob


class DuplicateBackgroundJobError(RuntimeError):
    """Raised when a job idempotency key is already reserved."""


class BackgroundJobNotFoundError(LookupError):
    """Raised when a background-job record cannot be found."""


class BackgroundJobStore(Protocol):
    async def reserve(self, idempotency_key: str, job_id: str) -> None: ...
    async def save(self, job: BackgroundJob) -> None: ...
    async def get(self, job_id: str) -> BackgroundJob | None: ...
    async def get_by_idempotency_key(self, idempotency_key: str) -> BackgroundJob | None: ...
    async def release(self, idempotency_key: str) -> None: ...


class InMemoryBackgroundJobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, BackgroundJob] = {}
        self._job_ids_by_key: dict[str, str] = {}
        self._reserved_keys: set[str] = set()
        self._lock = asyncio.Lock()

    async def reserve(self, idempotency_key: str, job_id: str) -> None:
        async with self._lock:
            if idempotency_key in self._reserved_keys or idempotency_key in self._job_ids_by_key:
                raise DuplicateBackgroundJobError(
                    "A background job with this idempotency key already exists."
                )
            self._reserved_keys.add(idempotency_key)
            self._job_ids_by_key[idempotency_key] = job_id

    async def save(self, job: BackgroundJob) -> None:
        async with self._lock:
            self._jobs[job.job_id] = job
            self._job_ids_by_key[job.idempotency_key] = job.job_id
            self._reserved_keys.discard(job.idempotency_key)

    async def get(self, job_id: str) -> BackgroundJob | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> BackgroundJob | None:
        async with self._lock:
            job_id = self._job_ids_by_key.get(idempotency_key)
            return self._jobs.get(job_id) if job_id is not None else None

    async def release(self, idempotency_key: str) -> None:
        async with self._lock:
            self._reserved_keys.discard(idempotency_key)
            job_id = self._job_ids_by_key.get(idempotency_key)
            if job_id is not None and job_id not in self._jobs:
                self._job_ids_by_key.pop(idempotency_key, None)


class RedisBackgroundJobStore:
    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        job_ttl_seconds: int,
        lock_ttl_seconds: int,
    ) -> None:
        if not key_prefix.strip():
            raise ValueError("key_prefix must not be empty.")
        if job_ttl_seconds <= 0:
            raise ValueError("job_ttl_seconds must be greater than zero.")
        if lock_ttl_seconds <= 0:
            raise ValueError("lock_ttl_seconds must be greater than zero.")
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.job_ttl_seconds = job_ttl_seconds
        self.lock_ttl_seconds = lock_ttl_seconds

    def _job_key(self, job_id: str) -> str:
        return f"{self.key_prefix}:job:{job_id}"

    def _idempotency_key(self, idempotency_key: str) -> str:
        return f"{self.key_prefix}:idempotency:{idempotency_key}"

    def _lock_key(self, idempotency_key: str) -> str:
        return f"{self.key_prefix}:lock:{idempotency_key}"

    @staticmethod
    def _serialize(job: BackgroundJob) -> str:
        payload = {
            "job_id": job.job_id,
            "idempotency_key": job.idempotency_key,
            "job_type": job.job_type,
            "status": job.status,
            "scope_id": job.scope_id,
            "account_id": job.account_id,
            "attempt_count": job.attempt_count,
            "max_attempts": job.max_attempts,
            "queued_at": job.queued_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "result": job.result,
            "error_type": job.error_type,
            "error_message": job.error_message,
            "retryable": job.retryable,
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _deserialize(payload: str | bytes) -> BackgroundJob:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data: dict[str, Any] = json.loads(payload)

        def parse_datetime(value: str | None) -> datetime | None:
            return datetime.fromisoformat(value) if value is not None else None

        return BackgroundJob(
            job_id=data["job_id"],
            idempotency_key=data["idempotency_key"],
            job_type=data["job_type"],
            status=data["status"],
            scope_id=data["scope_id"],
            account_id=data["account_id"],
            attempt_count=int(data["attempt_count"]),
            max_attempts=int(data["max_attempts"]),
            queued_at=datetime.fromisoformat(data["queued_at"]),
            started_at=parse_datetime(data["started_at"]),
            completed_at=parse_datetime(data["completed_at"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            result=data["result"],
            error_type=data["error_type"],
            error_message=data["error_message"],
            retryable=bool(data["retryable"]),
        )

    async def reserve(self, idempotency_key: str, job_id: str) -> None:
        acquired = await self.redis.set(
            self._lock_key(idempotency_key), job_id, nx=True, ex=self.lock_ttl_seconds
        )
        if not acquired:
            raise DuplicateBackgroundJobError(
                "A background job with this idempotency key is already running."
            )
        if await self.redis.get(self._idempotency_key(idempotency_key)) is not None:
            await self.release(idempotency_key)
            raise DuplicateBackgroundJobError(
                "A background job with this idempotency key already exists."
            )

    async def save(self, job: BackgroundJob) -> None:
        pipeline = self.redis.pipeline(transaction=True)
        pipeline.set(self._job_key(job.job_id), self._serialize(job), ex=self.job_ttl_seconds)
        pipeline.set(
            self._idempotency_key(job.idempotency_key), job.job_id, ex=self.job_ttl_seconds
        )
        pipeline.delete(self._lock_key(job.idempotency_key))
        try:
            await pipeline.execute()
        except Exception:
            await self.release(job.idempotency_key)
            raise

    async def get(self, job_id: str) -> BackgroundJob | None:
        payload = await self.redis.get(self._job_key(job_id))
        return self._deserialize(payload) if payload is not None else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> BackgroundJob | None:
        job_id = await self.redis.get(self._idempotency_key(idempotency_key))
        if job_id is None:
            return None
        if isinstance(job_id, bytes):
            job_id = job_id.decode("utf-8")
        return await self.get(job_id)

    async def release(self, idempotency_key: str) -> None:
        await self.redis.delete(self._lock_key(idempotency_key))
