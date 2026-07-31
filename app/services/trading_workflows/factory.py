from functools import lru_cache

from redis.asyncio import Redis

from app.core.config import Settings, get_settings
from app.services.trading_workflows.service import PaperTradingWorkflowService
from app.services.trading_workflows.store import (
    InMemoryTradingWorkflowStore,
    RedisTradingWorkflowStore,
    TradingWorkflowStore,
)


def _build(settings: Settings) -> TradingWorkflowStore:
    if settings.trading_workflow_store == "memory":
        return InMemoryTradingWorkflowStore()
    return RedisTradingWorkflowStore(
        Redis.from_url(settings.redis_url, decode_responses=False),
        prefix=settings.trading_workflow_key_prefix,
        ttl=settings.trading_workflow_ttl_seconds,
        lock_ttl=settings.trading_workflow_lock_ttl_seconds,
    )


@lru_cache(maxsize=1)
def _default() -> TradingWorkflowStore:
    return _build(get_settings())


def get_trading_workflow_service(settings: Settings | None = None) -> PaperTradingWorkflowService:
    resolved = settings or get_settings()
    return PaperTradingWorkflowService(_build(settings) if settings else _default(), resolved)


def get_trading_workflow_store(settings: Settings | None = None) -> TradingWorkflowStore:
    return _build(settings) if settings else _default()
