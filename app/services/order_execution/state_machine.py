from __future__ import annotations

from app.services.order_execution.models import ExecutionStatus


class InvalidExecutionTransitionError(RuntimeError):
    """Raised when an execution status transition is invalid."""


TERMINAL_STATUSES: frozenset[ExecutionStatus] = frozenset(
    {"FILLED", "CANCELLED", "REJECTED", "FAILED"}
)

ALLOWED_TRANSITIONS: dict[ExecutionStatus, frozenset[ExecutionStatus]] = {
    "CREATED": frozenset({"SUBMISSION_PENDING", "REJECTED", "FAILED"}),
    "SUBMISSION_PENDING": frozenset({"SUBMITTED", "REJECTED", "FAILED"}),
    "SUBMITTED": frozenset(
        {
            "ACKNOWLEDGED",
            "PARTIALLY_FILLED",
            "FILLED",
            "CANCEL_PENDING",
            "REJECTED",
            "FAILED",
        }
    ),
    "ACKNOWLEDGED": frozenset(
        {"PARTIALLY_FILLED", "FILLED", "CANCEL_PENDING", "REJECTED", "FAILED"}
    ),
    "PARTIALLY_FILLED": frozenset(
        {"PARTIALLY_FILLED", "FILLED", "CANCEL_PENDING", "FAILED"}
    ),
    "CANCEL_PENDING": frozenset(
        {"CANCELLED", "PARTIALLY_FILLED", "FILLED", "FAILED"}
    ),
    "FILLED": frozenset(),
    "CANCELLED": frozenset(),
    "REJECTED": frozenset(),
    "FAILED": frozenset(),
}


class OrderExecutionStateMachine:
    @staticmethod
    def is_terminal(status: ExecutionStatus) -> bool:
        return status in TERMINAL_STATUSES

    @staticmethod
    def can_transition(current: ExecutionStatus, target: ExecutionStatus) -> bool:
        return target in ALLOWED_TRANSITIONS[current]

    @classmethod
    def validate_transition(
        cls, current: ExecutionStatus, target: ExecutionStatus
    ) -> None:
        if current == target and current != "PARTIALLY_FILLED":
            raise InvalidExecutionTransitionError(
                f"Execution is already in status {current}."
            )
        if not cls.can_transition(current, target):
            raise InvalidExecutionTransitionError(
                f"Invalid execution transition: {current} -> {target}."
            )
