from app.services.trading_workflows.models import TradingWorkflowStatus


class InvalidWorkflowTransitionError(RuntimeError):
    """Raised for an invalid workflow transition."""


TERMINAL_WORKFLOW_STATUSES = frozenset({"RISK_REJECTED", "COMPLETED", "FAILED", "CANCELLED"})
ALLOWED_WORKFLOW_TRANSITIONS: dict[str, frozenset[str]] = {
    "CREATED": frozenset({"RECOMMENDATION_READY", "FAILED", "CANCELLED"}),
    "RECOMMENDATION_READY": frozenset({"RISK_APPROVED", "RISK_REJECTED", "FAILED", "CANCELLED"}),
    "RISK_APPROVED": frozenset({"AWAITING_APPROVAL", "APPROVED", "FAILED", "CANCELLED"}),
    "RISK_REJECTED": frozenset(),
    "AWAITING_APPROVAL": frozenset({"APPROVED", "FAILED", "CANCELLED"}),
    "APPROVED": frozenset({"INTENT_CREATED", "FAILED", "CANCELLED"}),
    "INTENT_CREATED": frozenset({"EXECUTION_CREATED", "FAILED", "CANCELLED"}),
    "EXECUTION_CREATED": frozenset({"SUBMISSION_PENDING", "FAILED", "CANCELLED"}),
    "SUBMISSION_PENDING": frozenset({"SUBMITTED", "FAILED", "CANCELLED"}),
    "SUBMITTED": frozenset({"PARTIALLY_FILLED", "FILLED", "FAILED", "CANCELLED"}),
    "PARTIALLY_FILLED": frozenset({"PARTIALLY_FILLED", "FILLED", "FAILED", "CANCELLED"}),
    "FILLED": frozenset({"POSITION_RECONCILED", "FAILED"}),
    "POSITION_RECONCILED": frozenset({"EXIT_MONITORING", "COMPLETED", "FAILED"}),
    "EXIT_MONITORING": frozenset({"EXIT_SIGNAL_CREATED", "COMPLETED", "FAILED", "CANCELLED"}),
    "EXIT_SIGNAL_CREATED": frozenset({"EXIT_INTENT_CREATED", "FAILED", "CANCELLED"}),
    "EXIT_INTENT_CREATED": frozenset({"EXIT_EXECUTION_CREATED", "FAILED", "CANCELLED"}),
    "EXIT_EXECUTION_CREATED": frozenset({"SUBMISSION_PENDING", "COMPLETED", "FAILED", "CANCELLED"}),
    "COMPLETED": frozenset(),
    "FAILED": frozenset({"CREATED"}),
    "CANCELLED": frozenset(),
}


class TradingWorkflowStateMachine:
    @staticmethod
    def is_terminal(status: TradingWorkflowStatus) -> bool:
        return status in TERMINAL_WORKFLOW_STATUSES

    @staticmethod
    def validate(current: TradingWorkflowStatus, target: TradingWorkflowStatus) -> None:
        if target not in ALLOWED_WORKFLOW_TRANSITIONS[current]:
            raise InvalidWorkflowTransitionError(
                f"Invalid workflow transition: {current} -> {target}."
            )
