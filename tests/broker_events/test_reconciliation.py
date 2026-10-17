import pytest

from tests.broker_events.test_service import Harness, report


@pytest.mark.asyncio
async def test_failed_event_is_applied_on_retry_once_the_order_exists() -> None:
    h = Harness()
    early = await h.service.ingest_execution(report("paper-intent-1", "e1", 2, 2))
    assert early.event.status == "FAILED"
    order = await h.submitted()
    assert order.broker_order_id == "paper-intent-1"
    assert await h.service.retry_failed_for_broker_order(order.broker_order_id) == 1
    event = await h.service.get(early.event.event_id)
    assert event is not None and event.status == "PROCESSED"
    assert event.attempt_count == 2
    assert (await h.executions.get(order.execution_id)).status == "FILLED"


@pytest.mark.asyncio
async def test_retries_stop_at_max_attempts() -> None:
    h = Harness()
    early = await h.service.ingest_execution(report("paper-never", "e1", 1, 1))
    await h.service.retry_failed_for_broker_order("paper-never")
    await h.service.retry_failed_for_broker_order("paper-never")
    event = await h.service.get(early.event.event_id)
    assert event is not None and event.status == "DEAD_LETTER"
    assert await h.service.retry_failed_for_broker_order("paper-never") == 0
