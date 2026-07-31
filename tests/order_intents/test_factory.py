from app.core.config import Settings
from app.services.order_intents.factory import get_order_intent_store
from app.services.order_intents.redis_store import RedisOrderIntentStore
from app.services.order_intents.store import InMemoryOrderIntentStore


def settings(store_type: str) -> Settings:
    return Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        order_intent_store=store_type,
    )


def test_factory_returns_memory_store() -> None:
    assert isinstance(
        get_order_intent_store(settings("memory")), InMemoryOrderIntentStore
    )


def test_factory_returns_redis_store() -> None:
    assert isinstance(get_order_intent_store(settings("redis")), RedisOrderIntentStore)
