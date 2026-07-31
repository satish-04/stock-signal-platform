from itertools import pairwise

import pytest

from app.services.trading_workflows import (
    InvalidWorkflowTransitionError,
    TradingWorkflowStateMachine,
)


def test_valid_entry_path() -> None:
    path = [
        "CREATED",
        "RECOMMENDATION_READY",
        "RISK_APPROVED",
        "AWAITING_APPROVAL",
        "APPROVED",
        "INTENT_CREATED",
        "EXECUTION_CREATED",
        "SUBMISSION_PENDING",
        "SUBMITTED",
        "FILLED",
        "POSITION_RECONCILED",
        "EXIT_MONITORING",
        "COMPLETED",
    ]
    for current, target in pairwise(path):
        TradingWorkflowStateMachine.validate(current, target)


def test_invalid_skip_is_rejected() -> None:
    with pytest.raises(InvalidWorkflowTransitionError):
        TradingWorkflowStateMachine.validate("CREATED", "SUBMITTED")
