import pytest

from app.services.order_execution import (
    InvalidExecutionTransitionError,
    OrderExecutionStateMachine,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("CREATED", "SUBMISSION_PENDING"),
        ("CREATED", "REJECTED"),
        ("SUBMISSION_PENDING", "SUBMITTED"),
        ("SUBMITTED", "ACKNOWLEDGED"),
        ("SUBMITTED", "PARTIALLY_FILLED"),
        ("SUBMITTED", "FILLED"),
        ("ACKNOWLEDGED", "PARTIALLY_FILLED"),
        ("ACKNOWLEDGED", "FILLED"),
        ("PARTIALLY_FILLED", "PARTIALLY_FILLED"),
        ("PARTIALLY_FILLED", "FILLED"),
        ("SUBMITTED", "CANCEL_PENDING"),
        ("ACKNOWLEDGED", "CANCEL_PENDING"),
        ("CANCEL_PENDING", "CANCELLED"),
        ("CANCEL_PENDING", "PARTIALLY_FILLED"),
        ("CANCEL_PENDING", "FILLED"),
    ],
)
def test_valid_transitions(current, target) -> None:
    OrderExecutionStateMachine.validate_transition(current, target)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        ("CREATED", "FILLED"),
        ("CREATED", "CANCELLED"),
        ("SUBMISSION_PENDING", "FILLED"),
        ("ACKNOWLEDGED", "SUBMITTED"),
        ("PARTIALLY_FILLED", "ACKNOWLEDGED"),
        ("FILLED", "CANCELLED"),
        ("CANCELLED", "SUBMITTED"),
        ("REJECTED", "SUBMITTED"),
        ("FAILED", "SUBMITTED"),
    ],
)
def test_invalid_transitions(current, target) -> None:
    with pytest.raises(InvalidExecutionTransitionError):
        OrderExecutionStateMachine.validate_transition(current, target)


@pytest.mark.parametrize("status", ["FILLED", "CANCELLED", "REJECTED", "FAILED"])
def test_terminal_statuses(status) -> None:
    assert OrderExecutionStateMachine.is_terminal(status)


def test_repeated_non_partial_status_is_rejected() -> None:
    with pytest.raises(InvalidExecutionTransitionError, match="already in status"):
        OrderExecutionStateMachine.validate_transition("SUBMITTED", "SUBMITTED")
