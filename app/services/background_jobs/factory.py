from __future__ import annotations

from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.background_jobs.store import (
    BackgroundJobStore,
    InMemoryBackgroundJobStore,
    RedisBackgroundJobStore,
)


def _build_background_job_store(settings: Settings) -> BackgroundJobStore:
    if settings.background_job_store == "memory":
        return InMemoryBackgroundJobStore()
    redis = Redis.from_url(settings.redis_url, decode_responses=False)
    return RedisBackgroundJobStore(
        redis=redis,
        key_prefix=settings.background_job_key_prefix,
        job_ttl_seconds=settings.background_job_ttl_seconds,
        lock_ttl_seconds=settings.background_job_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _get_default_background_job_store() -> BackgroundJobStore:
    return _build_background_job_store(get_settings())


def get_background_job_store(settings: Settings | None = None) -> BackgroundJobStore:
    return _build_background_job_store(settings) if settings else _get_default_background_job_store()


def clear_background_job_store_cache() -> None:
    _get_default_background_job_store.cache_clear()
