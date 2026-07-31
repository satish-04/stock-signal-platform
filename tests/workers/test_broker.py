from dramatiq.brokers.redis import RedisBroker

from app.workers.broker import create_dramatiq_broker


def test_create_dramatiq_broker() -> None:
    assert isinstance(create_dramatiq_broker(), RedisBroker)


def test_broker_contains_retry_middleware() -> None:
    broker = create_dramatiq_broker()
    middleware_names = {type(middleware).__name__ for middleware in broker.middleware}
    assert {"Retries", "TimeLimit", "AgeLimit"} <= middleware_names
