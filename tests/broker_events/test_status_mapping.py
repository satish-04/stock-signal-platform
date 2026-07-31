import pytest

from app.services.broker_events import normalize_ibkr_order_status


@pytest.mark.parametrize(
    ("raw_status", "expected"),
    [
        ("PendingSubmit", "PENDING_SUBMIT"), ("PendingCancel", "PENDING_CANCEL"),
        ("PreSubmitted", "PRE_SUBMITTED"), ("Submitted", "SUBMITTED"),
        ("ApiCancelled", "API_CANCELLED"), ("Cancelled", "CANCELLED"),
        ("Filled", "FILLED"), ("Inactive", "INACTIVE"),
        (" submitted ", "SUBMITTED"), ("unknown-status", "UNKNOWN"),
    ],
)
def test_normalize_ibkr_order_status(raw_status: str, expected: str) -> None:
    assert normalize_ibkr_order_status(raw_status) == expected
