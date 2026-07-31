from datetime import UTC, datetime, timedelta
from functools import lru_cache

from app.core.config import get_settings
from app.services.background_jobs import BackgroundSweepService, SweepDefinition
from app.workers.concrete_sweep_adapters import (
    ConcreteExecutionSweepAdapter,
    ConcretePositionSweepAdapter,
    ConcreteWorkflowSweepAdapter,
)


@lru_cache(maxsize=1)
def get_background_sweep_service() -> BackgroundSweepService:
    settings = get_settings()
    workflows = ConcreteWorkflowSweepAdapter(settings)
    executions = ConcreteExecutionSweepAdapter(settings)
    positions = ConcretePositionSweepAdapter(settings)

    async def workflow_ids() -> list[str]:
        return [c.candidate_id for c in await workflows.list_reconciliation_candidates()]

    async def execution_ids() -> list[str]:
        return [c.candidate_id for c in await executions.list_reconciliation_candidates()]

    async def position_ids() -> list[str]:
        return [c.candidate_id for c in await positions.list_reconciliation_candidates()]

    async def exit_ids() -> list[str]:
        return [c.candidate_id for c in await positions.list_exit_candidates()]

    async def stale_ids() -> list[str]:
        cutoff = datetime.now(UTC) - timedelta(seconds=settings.background_sweep_stale_workflow_seconds)
        return [c.candidate_id for c in await workflows.list_stale_candidates(cutoff)]

    return BackgroundSweepService(
        workflow_reconciliation=SweepDefinition(workflow_ids, workflows.reconcile, "No workflows require reconciliation.", "Workflow reconciliation completed."),
        execution_reconciliation=SweepDefinition(execution_ids, executions.reconcile, "No executions require reconciliation.", "Execution reconciliation completed."),
        position_reconciliation=SweepDefinition(position_ids, positions.reconcile, "No fills require position reconciliation.", "Position reconciliation completed."),
        exit_monitoring=SweepDefinition(exit_ids, positions.monitor_exit, "No open positions require exit monitoring.", "Exit monitoring completed."),
        stale_workflow_cleanup=SweepDefinition(stale_ids, workflows.handle_stale, "No stale workflows found.", "Stale workflow cleanup completed."),
    )
