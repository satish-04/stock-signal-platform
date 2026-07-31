from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

OrderIntentStatus = Literal[
    "PENDING",
    "APPROVED",
    "REJECTED",
    "SUBMITTED",
    "DUPLICATE",
    "FAILED",
]


@dataclass(frozen=True)
class OrderIntent:
    intent_id: str
    idempotency_key: str
    symbol: str
    option_symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["LIMIT"]
    quantity: int
    limit_price: Decimal
    estimated_debit: Decimal
    maximum_loss: Decimal
    stop_price: Decimal
    first_target_price: Decimal
    second_target_price: Decimal
    status: OrderIntentStatus
    created_at: datetime
    reasons: tuple[str, ...]
    rejection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class OrderSubmissionResult:
    intent: OrderIntent
    broker_response: dict | None
