import pytest

from app.core.config import Settings
from app.services.trading_workflows import (
    DuplicateTradingWorkflowError,
    InMemoryTradingWorkflowStore,
    PaperTradingWorkflowService,
    WorkflowApprovalError,
)


def service(max_attempts=3):
    settings = Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        trading_workflow_store="memory",
        paper_workflow_max_attempts=max_attempts,
    )
    return PaperTradingWorkflowService(InMemoryTradingWorkflowStore(), settings)


@pytest.mark.asyncio
async def test_create_is_idempotent() -> None:
    subject = service()
    workflow = await subject.create("key", "ENTRY", "paper", "AAPL")
    assert workflow.status == "CREATED" and len(workflow.events) == 1
    with pytest.raises(DuplicateTradingWorkflowError):
        await subject.create("key", "ENTRY", "paper", "AAPL")


@pytest.mark.asyncio
async def test_manual_approval_gate() -> None:
    subject = service()
    workflow = await subject.create("key", "ENTRY", "paper", "AAPL")
    for status in ("RECOMMENDATION_READY", "RISK_APPROVED", "AWAITING_APPROVAL"):
        workflow = await subject.transition(workflow.workflow_id, status)
    with pytest.raises(WorkflowApprovalError):
        await subject.transition(workflow.workflow_id, "APPROVED")
    workflow = await subject.approve(workflow.workflow_id, "operator@example.com")
    assert workflow.status == "APPROVED" and workflow.approved_by


@pytest.mark.asyncio
async def test_retryable_failure_resumes() -> None:
    subject = service()
    workflow = await subject.create("retry", "ENTRY", "paper", "AAPL")
    workflow = await subject.fail(workflow.workflow_id, "BROKER", "temporary", True)
    assert workflow.status == "FAILED" and workflow.attempt_count == 1
    workflow = await subject.retry(workflow.workflow_id)
    assert workflow.status == "CREATED"
