from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.brokers.base import BrokerAdapter
from app.services.order_execution.service import PaperOrderExecutionService
from app.services.order_execution.store import (
    InMemoryOrderExecutionStore,
    OrderExecutionStore,
    RedisOrderExecutionStore,
)


def _build_store(settings: Settings) -> OrderExecutionStore:
    if settings.order_intent_store == "memory":
        return InMemoryOrderExecutionStore()
    return RedisOrderExecutionStore(
        Redis.from_url(settings.redis_url, decode_responses=False),
        key_prefix=settings.order_execution_key_prefix,
        execution_ttl_seconds=settings.order_execution_ttl_seconds,
        lock_ttl_seconds=settings.order_execution_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _default_store() -> OrderExecutionStore:
    return _build_store(get_settings())


def get_order_execution_store(settings: Settings | None = None) -> OrderExecutionStore:
    return _build_store(settings) if settings else _default_store()


def get_order_execution_service(
    broker: BrokerAdapter,
    *,
    settings: Settings | None = None,
    store: OrderExecutionStore | None = None,
) -> PaperOrderExecutionService:
    resolved = settings or get_settings()
    return PaperOrderExecutionService(
        broker, store or get_order_execution_store(settings), resolved
    )


def clear_order_execution_store_cache() -> None:
    _default_store.cache_clear()
