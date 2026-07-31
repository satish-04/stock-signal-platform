from app.services.broker_events.models import NormalizedOrderStatus

IBKR_STATUS_MAPPING: dict[str, NormalizedOrderStatus] = {
    "pendingsubmit": "PENDING_SUBMIT",
    "pendingcancel": "PENDING_CANCEL",
    "presubmitted": "PRE_SUBMITTED",
    "submitted": "SUBMITTED",
    "apicancelled": "API_CANCELLED",
    "cancelled": "CANCELLED",
    "filled": "FILLED",
    "inactive": "INACTIVE",
}


def normalize_ibkr_order_status(status: str) -> NormalizedOrderStatus:
    normalized = "".join(character for character in status.strip().lower() if character.isalnum())
    return IBKR_STATUS_MAPPING.get(normalized, "UNKNOWN")
