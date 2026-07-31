from datetime import UTC, datetime

import pytest

from app.services.background_jobs.models import BackgroundJob
from app.services.background_jobs.store import (
    DuplicateBackgroundJobError,
    InMemoryBackgroundJobStore,
    RedisBackgroundJobStore,
)


class FakePipeline:
    def __init__(self, redis: "FakeRedis") -> None:
        self.redis = redis
        self.operations: list[tuple] = []

    def set(self, key, value, *, ex=None):
        self.operations.append(("set", key, value, ex))
        return self

    def delete(self, key):
        self.operations.append(("delete", key))
        return self

    async def execute(self):
        results = []
        for operation in self.operations:
            if operation[0] == "set":
                _, key, value, ex = operation
                results.append(await self.redis.set(key, value, ex=ex))
            else:
                results.append(await self.redis.delete(operation[1]))
        return results


class FakeRedis:
    def __init__(self) -> None:
        self.data = {}
        self.ttls = {}

    async def set(self, key, value, *, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        if ex is not None:
            self.ttls[key] = ex
        return True

    async def get(self, key):
        return self.data.get(key)

    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                deleted += 1
            self.ttls.pop(key, None)
        return deleted

    def pipeline(self, *, transaction=True):
        assert transaction is True
        return FakePipeline(self)


def build_job() -> BackgroundJob:
    now = datetime.now(UTC)
    return BackgroundJob(
        "job-1", "key-1", "WORKFLOW_RECONCILIATION", "QUEUED", None,
        "paper-account", 0, 3, now, None, None, now, now, None, None, None, True
    )


@pytest.mark.asyncio
async def test_memory_store_duplicate_lock() -> None:
    store = InMemoryBackgroundJobStore()
    await store.reserve("key-1", "job-1")
    with pytest.raises(DuplicateBackgroundJobError):
        await store.reserve("key-1", "job-2")


@pytest.mark.asyncio
async def test_redis_store_round_trip() -> None:
    redis = FakeRedis()
    store = RedisBackgroundJobStore(
        redis=redis, key_prefix="test:jobs", job_ttl_seconds=3600, lock_ttl_seconds=60
    )
    job = build_job()
    await store.reserve(job.idempotency_key, job.job_id)
    await store.save(job)
    assert await store.get(job.job_id) == job
    assert await store.get_by_idempotency_key(job.idempotency_key) == job


def test_serialization_round_trip() -> None:
    job = build_job()
    restored = RedisBackgroundJobStore._deserialize(RedisBackgroundJobStore._serialize(job))
    assert restored == job
    assert restored.created_at.tzinfo is not None
