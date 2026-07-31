from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.position_exits.service import PositionExitMonitoringService
from app.services.position_exits.store import (
    InMemoryPositionExitStore,
    PositionExitStore,
    RedisPositionExitStore,
)


def _build(settings: Settings) -> PositionExitStore:
    if settings.position_exit_store == "memory":
        return InMemoryPositionExitStore()
    return RedisPositionExitStore(
        Redis.from_url(settings.redis_url, decode_responses=False),
        prefix=settings.position_exit_key_prefix,
        ttl=settings.position_exit_ttl_seconds,
        lock_ttl=settings.position_exit_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _default() -> PositionExitStore:
    return _build(get_settings())


def get_position_exit_service(settings: Settings | None = None) -> PositionExitMonitoringService:
    resolved = settings or get_settings()
    return PositionExitMonitoringService(_build(settings) if settings else _default(), resolved)
