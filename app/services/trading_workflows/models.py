from dataclasses import dataclass
from datetime import datetime
from typing import Literal

TradingWorkflowStatus = Literal[
    "CREATED",
    "RECOMMENDATION_READY",
    "RISK_APPROVED",
    "RISK_REJECTED",
    "AWAITING_APPROVAL",
    "APPROVED",
    "INTENT_CREATED",
    "EXECUTION_CREATED",
    "SUBMISSION_PENDING",
    "SUBMITTED",
    "PARTIALLY_FILLED",
    "FILLED",
    "POSITION_RECONCILED",
    "EXIT_MONITORING",
    "EXIT_SIGNAL_CREATED",
    "EXIT_INTENT_CREATED",
    "EXIT_EXECUTION_CREATED",
    "COMPLETED",
    "FAILED",
    "CANCELLED",
]
TradingWorkflowType = Literal["ENTRY", "EXIT"]
WorkflowFailureType = Literal[
    "VALIDATION",
    "RISK_REJECTION",
    "DUPLICATE",
    "BROKER",
    "PERSISTENCE",
    "RECONCILIATION",
    "CONFIGURATION",
    "UNKNOWN",
]


@dataclass(frozen=True)
class WorkflowReference:
    recommendation_symbol: str | None = None
    order_intent_id: str | None = None
    execution_id: str | None = None
    position_id: str | None = None
    exit_signal_id: str | None = None
    parent_workflow_id: str | None = None


@dataclass(frozen=True)
class WorkflowFailure:
    failure_type: WorkflowFailureType
    message: str
    retryable: bool
    occurred_at: datetime


@dataclass(frozen=True)
class WorkflowEvent:
    event_id: str
    workflow_id: str
    previous_status: TradingWorkflowStatus | None
    new_status: TradingWorkflowStatus
    event_type: str
    message: str | None
    created_at: datetime


@dataclass(frozen=True)
class TradingWorkflow:
    workflow_id: str
    idempotency_key: str
    workflow_type: TradingWorkflowType
    status: TradingWorkflowStatus
    account_id: str
    symbol: str
    reference: WorkflowReference
    attempt_count: int
    max_attempts: int
    approval_required: bool
    approved_by: str | None
    approved_at: datetime | None
    failure: WorkflowFailure | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    events: tuple[WorkflowEvent, ...]
