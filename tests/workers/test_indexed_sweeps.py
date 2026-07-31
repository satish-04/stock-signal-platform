from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from app.services.order_execution.models import OrderExecution
from app.services.order_execution.store import InMemoryOrderExecutionStore
from app.services.positions.models import Position
from app.services.positions.store import InMemoryPositionStore
from app.services.trading_workflows.models import TradingWorkflow, WorkflowReference
from app.services.trading_workflows.store import InMemoryTradingWorkflowStore


async def test_workflow_indexes_move_and_resolve_references() -> None:
    now = datetime.now(UTC)
    store = InMemoryTradingWorkflowStore()
    workflow = TradingWorkflow(
        "workflow-1", "key", "ENTRY", "CREATED", "paper", "AAPL",
        WorkflowReference(execution_id="execution-1", position_id="position-1"),
        0, 3, True, None, None, None, now, now, None, (),
    )
    await store.save(workflow)
    await store.save(replace(workflow, status="APPROVED", updated_at=now + timedelta(seconds=1)))
    assert await store.list_ids_by_statuses(("CREATED",), limit=10) == []
    assert await store.list_ids_by_statuses(("APPROVED",), limit=10) == ["workflow-1"]
    assert await store.get_by_execution_id("execution-1") == replace(
        workflow, status="APPROVED", updated_at=now + timedelta(seconds=1)
    )
    assert await store.get_by_position_id("position-1") is not None
    assert await store.list_account_ids(limit=10) == ["paper"]


async def test_execution_and_position_status_indexes() -> None:
    now = datetime.now(UTC)
    executions = InMemoryOrderExecutionStore()
    execution = OrderExecution(
        "execution-1", "intent-1", "key", "AAPL", "AAPL-CALL", "BUY", "LIMIT",
        1, Decimal(5), "SUBMITTED", None, None, 0, 1, None, now, None, None,
        now, now, None, None,
    )
    await executions.save(execution)
    assert await executions.list_ids_by_statuses(("SUBMITTED",), limit=10) == ["execution-1"]

    positions = InMemoryPositionStore()
    position = Position(
        "position-1", "paper", "AAPL", "AAPL-CALL", "LONG", "OPEN", 1, 100,
        Decimal(5), Decimal(6), Decimal(500), Decimal(600), Decimal(0), Decimal(100),
        now, now, None,
    )
    await positions.save_position(position)
    assert await positions.list_ids_by_statuses(("OPEN",), limit=10) == ["position-1"]
    assert await positions.list_account_ids(limit=10) == ["paper"]


def test_sweep_code_does_not_use_redis_scan() -> None:
    source = "\n".join(
        Path(path).read_text()
        for path in (
            "app/workers/sweep_factory.py",
            "app/workers/concrete_sweep_adapters.py",
        )
    ).lower()
    assert ".scan(" not in source
    assert ".scan_iter(" not in source
