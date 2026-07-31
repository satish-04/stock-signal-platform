from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.services.background_jobs import SweepCandidate
from app.services.background_jobs.candidates import (
    EXECUTION_RECONCILIATION_STATUSES,
    NON_TERMINAL_WORKFLOW_STATUSES,
    POSITION_RECONCILIATION_STATUSES,
    WORKFLOW_RECONCILIATION_STATUSES,
)
from app.services.order_execution.factory import (
    get_order_execution_service,
    get_order_execution_store,
)
from app.services.position_exits.factory import get_position_exit_service
from app.services.position_exits.models import PositionExitContext
from app.services.positions.factory import get_position_store
from app.services.trading_workflows.factory import (
    get_trading_workflow_service,
    get_trading_workflow_store,
)


class ConcreteWorkflowSweepAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = get_trading_workflow_store(settings)
        self.service = get_trading_workflow_service(settings)

    async def list_reconciliation_candidates(self) -> list[SweepCandidate]:
        ids = await self.store.list_ids_by_statuses(
            WORKFLOW_RECONCILIATION_STATUSES, limit=self.settings.background_sweep_batch_size
        )
        return [
            SweepCandidate(w.workflow_id, "WORKFLOW", w.status, w.account_id, w.updated_at)
            for workflow_id in ids
            for w in [await self.service.get(workflow_id)]
        ]

    async def reconcile(self, workflow_id: str) -> str | None:
        workflow = await self.service.get(workflow_id)
        if workflow.status in {"AWAITING_APPROVAL", "RISK_APPROVED"}:
            return None
        if not self.settings.paper_workflow_auto_submit and workflow.status in {
            "EXECUTION_CREATED", "SUBMISSION_PENDING"
        }:
            return None
        return f"workflow remains {workflow.status}; awaiting persisted downstream event"

    async def list_stale_candidates(self, stale_before: datetime) -> list[SweepCandidate]:
        ids = await self.store.list_ids_updated_before(
            NON_TERMINAL_WORKFLOW_STATUSES,
            updated_before=stale_before,
            limit=self.settings.background_sweep_batch_size,
        )
        return [
            SweepCandidate(w.workflow_id, "WORKFLOW", w.status, w.account_id, w.updated_at)
            for workflow_id in ids
            for w in [await self.service.get(workflow_id)]
        ]

    async def handle_stale(self, workflow_id: str) -> str | None:
        workflow = await self.service.get(workflow_id)
        if workflow.status == "AWAITING_APPROVAL":
            return None
        failed = await self.service.fail(
            workflow_id, "RECONCILIATION", "Workflow exceeded background staleness threshold.", True
        )
        return f"workflow marked {failed.status}"


class ConcreteExecutionSweepAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.store = get_order_execution_store(settings)
        self.service = get_order_execution_service(settings)

    async def list_reconciliation_candidates(self) -> list[SweepCandidate]:
        ids = await self.store.list_ids_by_statuses(
            EXECUTION_RECONCILIATION_STATUSES, limit=self.settings.background_sweep_batch_size
        )
        return [
            SweepCandidate(e.execution_id, "EXECUTION", e.status, None, e.updated_at)
            for execution_id in ids
            for e in [await self.service.get(execution_id)]
        ]

    async def reconcile(self, execution_id: str) -> str | None:
        execution = await self.service.get(execution_id)
        if not self.settings.paper_workflow_auto_submit and execution.status == "SUBMISSION_PENDING":
            return None
        return f"execution remains {execution.status}; awaiting persisted broker callback"


class ConcretePositionSweepAdapter:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.execution_store = get_order_execution_store(settings)
        self.execution_service = get_order_execution_service(settings)
        self.position_store = get_position_store(settings)
        self.exit_service = get_position_exit_service(settings)

    async def list_reconciliation_candidates(self) -> list[SweepCandidate]:
        ids = await self.execution_store.list_ids_by_statuses(
            POSITION_RECONCILIATION_STATUSES, limit=self.settings.background_sweep_batch_size
        )
        return [
            SweepCandidate(e.execution_id, "EXECUTION", e.status, None, e.updated_at)
            for execution_id in ids
            for e in [await self.execution_service.get(execution_id)]
        ]

    async def reconcile(self, execution_id: str) -> str | None:
        del execution_id
        return None

    async def list_exit_candidates(self) -> list[SweepCandidate]:
        ids = await self.position_store.list_ids_by_statuses(
            ("OPEN",), limit=self.settings.background_sweep_batch_size
        )
        candidates = []
        for position_id in ids:
            position = await self.position_store.get_position(position_id)
            if position is not None:
                candidates.append(
                    SweepCandidate(position.position_id, "POSITION", position.status, position.account_id, position.updated_at)
                )
        return candidates

    async def monitor_exit(self, position_id: str) -> str | None:
        position = await self.position_store.get_position(position_id)
        if position is None or position.status != "OPEN" or position.current_mark_price is None:
            return None
        now = datetime.now(UTC)
        signal = await self.exit_service.monitor(
            PositionExitContext(
                position.position_id, position.account_id, position.symbol, position.option_symbol,
                position.quantity, position.multiplier, position.average_entry_price,
                position.current_mark_price, position.current_mark_price, position.opened_at,
                now, position.updated_at, None, False,
            )
        )
        return None if signal is None else f"exit signal {signal.exit_signal_id} created"
