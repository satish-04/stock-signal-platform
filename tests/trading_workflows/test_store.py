from datetime import UTC, datetime

from app.services.trading_workflows import TradingWorkflow, WorkflowReference
from app.services.trading_workflows.store import RedisTradingWorkflowStore


def test_redis_serialization_round_trip() -> None:
    now = datetime.now(UTC)
    workflow = TradingWorkflow(
        "w",
        "k",
        "ENTRY",
        "CREATED",
        "paper",
        "AAPL",
        WorkflowReference(),
        0,
        3,
        True,
        None,
        None,
        None,
        now,
        now,
        None,
        (),
    )
    assert (
        RedisTradingWorkflowStore._deserialize(RedisTradingWorkflowStore._serialize(workflow))
        == workflow
    )
