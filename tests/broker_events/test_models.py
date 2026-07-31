from datetime import UTC, datetime
from decimal import Decimal

from app.services.broker_events import BrokerOrderStatusPayload


def test_order_status_payload_is_typed() -> None:
    payload = BrokerOrderStatusPayload(
        "1", "Submitted", "SUBMITTED", Decimal(0), Decimal(1), None,
        None, None, None, None, None, None,
    )
    assert payload.normalized_status == "SUBMITTED"
    assert datetime.now(UTC).tzinfo is not None
