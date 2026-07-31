from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.order_intents.redis_store import RedisOrderIntentStore
from app.services.order_intents.store import InMemoryOrderIntentStore, OrderIntentStore


def get_order_intent_store(settings: Settings | None = None) -> OrderIntentStore:
    resolved = settings or get_settings()
    if resolved.order_intent_store == "memory":
        return InMemoryOrderIntentStore()
    redis = Redis.from_url(resolved.redis_url, decode_responses=False)
    return RedisOrderIntentStore(
        redis,
        key_prefix=resolved.order_intent_key_prefix,
        intent_ttl_seconds=resolved.order_intent_ttl_seconds,
        lock_ttl_seconds=resolved.order_intent_lock_ttl_seconds,
    )
