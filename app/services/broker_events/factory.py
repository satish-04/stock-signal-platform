from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.broker_events.service import BrokerEventService
from app.services.broker_events.store import (
    BrokerEventStore,
    InMemoryBrokerEventStore,
    RedisBrokerEventStore,
)
from app.services.brokers.base import BrokerAdapter
from app.services.brokers.factory import get_broker
from app.services.order_execution.factory import get_order_execution_service
from app.services.positions.factory import get_position_service


def _build_store(settings: Settings) -> BrokerEventStore:
    if settings.broker_event_store == "memory":
        return InMemoryBrokerEventStore()
    return RedisBrokerEventStore(
        Redis.from_url(settings.redis_url, decode_responses=False),
        key_prefix=settings.broker_event_key_prefix,
        event_ttl_seconds=settings.broker_event_ttl_seconds,
        lock_ttl_seconds=settings.broker_event_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _default_store() -> BrokerEventStore:
    return _build_store(get_settings())


def get_broker_event_store(settings: Settings | None = None) -> BrokerEventStore:
    return _build_store(settings) if settings else _default_store()


def get_broker_event_service(
    broker: BrokerAdapter | None = None, settings: Settings | None = None
) -> BrokerEventService:
    resolved = settings or get_settings()
    return BrokerEventService(
        get_broker_event_store(settings),
        get_order_execution_service(broker or get_broker(), settings=settings),
        get_position_service(settings),
        resolved,
    )


def clear_broker_event_store_cache() -> None:
    _default_store.cache_clear()
