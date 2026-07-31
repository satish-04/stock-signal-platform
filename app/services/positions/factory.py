from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.positions.service import PaperPositionService
from app.services.positions.store import InMemoryPositionStore, PositionStore, RedisPositionStore


def _build_store(settings: Settings) -> PositionStore:
    if settings.position_store == "memory":
        return InMemoryPositionStore()
    return RedisPositionStore(
        Redis.from_url(settings.redis_url, decode_responses=False),
        key_prefix=settings.position_key_prefix,
        position_ttl_seconds=settings.position_ttl_seconds,
        fill_lock_ttl_seconds=settings.position_fill_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _default_store() -> PositionStore:
    return _build_store(get_settings())


def get_position_store(settings: Settings | None = None) -> PositionStore:
    return _build_store(settings) if settings else _default_store()


def get_position_service(settings: Settings | None = None) -> PaperPositionService:
    resolved = settings or get_settings()
    return PaperPositionService(get_position_store(settings), resolved)


def clear_position_store_cache() -> None:
    _default_store.cache_clear()
