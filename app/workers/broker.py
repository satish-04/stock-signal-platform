from __future__ import annotations

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import AgeLimit, Callbacks, Pipelines, Retries, TimeLimit

from app.core.config import get_settings


def create_dramatiq_broker() -> RedisBroker:
    settings = get_settings()
    broker = RedisBroker(url=settings.redis_url)
    broker.add_middleware(AgeLimit(max_age=15 * 60 * 1000))
    broker.add_middleware(TimeLimit(time_limit=5 * 60 * 1000))
    broker.add_middleware(
        Retries(
            max_retries=settings.worker_max_retries,
            min_backoff=settings.worker_retry_delay_seconds * 1000,
            max_backoff=settings.worker_retry_delay_seconds * 8 * 1000,
        )
    )
    broker.add_middleware(Callbacks())
    broker.add_middleware(Pipelines())
    return broker


broker = create_dramatiq_broker()
dramatiq.set_broker(broker)
