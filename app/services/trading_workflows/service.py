import hashlib
from dataclasses import replace
from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.services.trading_workflows.models import (
    TradingWorkflow,
    TradingWorkflowStatus,
    TradingWorkflowType,
    WorkflowEvent,
    WorkflowFailure,
    WorkflowFailureType,
    WorkflowReference,
)
from app.services.trading_workflows.state_machine import TradingWorkflowStateMachine
from app.services.trading_workflows.store import TradingWorkflowNotFoundError, TradingWorkflowStore


class WorkflowApprovalError(PermissionError):
    """Raised when manual workflow approval is invalid."""


class PaperTradingWorkflowService:
    def __init__(self, store: TradingWorkflowStore, settings: Settings | None = None) -> None:
        self.store, self.settings = store, settings or get_settings()

    @staticmethod
    def _event(
        workflow_id: str, previous, new, event_type: str, message: str | None = None
    ) -> WorkflowEvent:
        now = datetime.now(UTC)
        digest = hashlib.sha256(f"{workflow_id}|{new}|{now.isoformat()}".encode()).hexdigest()
        return WorkflowEvent(
            f"event_{digest[:24]}", workflow_id, previous, new, event_type, message, now
        )

    async def create(
        self,
        key: str,
        workflow_type: TradingWorkflowType,
        account_id: str,
        symbol: str,
        reference: WorkflowReference | None = None,
    ) -> TradingWorkflow:
        if self.settings.trading_mode != "paper":
            raise WorkflowApprovalError("Workflows are restricted to paper mode.")
        digest = hashlib.sha256(key.encode()).hexdigest()
        workflow_id = f"workflow_{digest[:24]}"
        await self.store.reserve(digest, workflow_id)
        now = datetime.now(UTC)
        event = self._event(workflow_id, None, "CREATED", "WORKFLOW_CREATED")
        workflow = TradingWorkflow(
            workflow_id,
            digest,
            workflow_type,
            "CREATED",
            account_id,
            symbol.upper(),
            reference or WorkflowReference(),
            0,
            self.settings.paper_workflow_max_attempts,
            self.settings.paper_workflow_require_manual_approval,
            None,
            None,
            None,
            now,
            now,
            None,
            (event,),
        )
        await self.store.save(workflow)
        return workflow

    async def get(self, workflow_id: str) -> TradingWorkflow:
        workflow = await self.store.get(workflow_id)
        if workflow is None:
            raise TradingWorkflowNotFoundError(f"Workflow {workflow_id!r} was not found.")
        return workflow

    async def transition(
        self,
        workflow_id: str,
        status: TradingWorkflowStatus,
        *,
        message: str | None = None,
        reference: WorkflowReference | None = None,
    ) -> TradingWorkflow:
        workflow = await self.get(workflow_id)
        TradingWorkflowStateMachine.validate(workflow.status, status)
        if status == "APPROVED" and workflow.approval_required and not workflow.approved_by:
            raise WorkflowApprovalError("Manual approval is required.")
        now = datetime.now(UTC)
        completed = now if TradingWorkflowStateMachine.is_terminal(status) else None
        event = self._event(workflow_id, workflow.status, status, "STATUS_CHANGED", message)
        updated = replace(
            workflow,
            status=status,
            reference=reference or workflow.reference,
            updated_at=now,
            completed_at=completed,
            failure=None if status != "FAILED" else workflow.failure,
            events=(*workflow.events, event),
        )
        await self.store.save(updated)
        return updated

    async def approve(self, workflow_id: str, approved_by: str) -> TradingWorkflow:
        if not approved_by.strip():
            raise WorkflowApprovalError("approved_by is required.")
        workflow = await self.get(workflow_id)
        if workflow.status != "AWAITING_APPROVAL":
            raise WorkflowApprovalError("Workflow is not awaiting approval.")
        now = datetime.now(UTC)
        approved = replace(
            workflow, approved_by=approved_by.strip(), approved_at=now, updated_at=now
        )
        await self.store.save(approved)
        return await self.transition(
            workflow_id, "APPROVED", message="Manual paper approval granted."
        )

    async def fail(
        self, workflow_id: str, failure_type: WorkflowFailureType, message: str, retryable: bool
    ) -> TradingWorkflow:
        workflow = await self.get(workflow_id)
        now = datetime.now(UTC)
        failure = WorkflowFailure(failure_type, message, retryable, now)
        updated = replace(workflow, failure=failure, attempt_count=workflow.attempt_count + 1)
        await self.store.save(updated)
        return await self.transition(workflow_id, "FAILED", message=message)

    async def retry(self, workflow_id: str) -> TradingWorkflow:
        workflow = await self.get(workflow_id)
        if workflow.status != "FAILED" or not workflow.failure or not workflow.failure.retryable:
            raise RuntimeError("Workflow failure is not retryable.")
        if workflow.attempt_count >= workflow.max_attempts:
            raise RuntimeError("Maximum workflow attempts reached.")
        return await self.transition(workflow_id, "CREATED", message="Workflow resumed for retry.")

    async def list_for_account(self, account_id: str) -> list[TradingWorkflow]:
        return sorted(await self.store.list_for_account(account_id), key=lambda w: w.created_at)
