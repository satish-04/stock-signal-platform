from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

ExecutionStatus = Literal[
    "CREATED",
    "SUBMISSION_PENDING",
    "SUBMITTED",
    "ACKNOWLEDGED",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCEL_PENDING",
    "CANCELLED",
    "REJECTED",
    "FAILED",
]

TerminalExecutionStatus = Literal["FILLED", "CANCELLED", "REJECTED", "FAILED"]


@dataclass(frozen=True)
class OrderExecution:
    execution_id: str
    intent_id: str
    idempotency_key: str
    symbol: str
    option_symbol: str
    side: Literal["BUY", "SELL"]
    order_type: Literal["LIMIT"]
    requested_quantity: int
    limit_price: Decimal
    status: ExecutionStatus
    broker_order_id: str | None
    broker_status: str | None
    filled_quantity: int
    remaining_quantity: int
    average_fill_price: Decimal | None
    submitted_at: datetime | None
    acknowledged_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    status_reason: str | None
    broker_response: dict | None


@dataclass(frozen=True)
class ExecutionUpdate:
    status: ExecutionStatus
    broker_order_id: str | None = None
    broker_status: str | None = None
    filled_quantity: int | None = None
    remaining_quantity: int | None = None
    average_fill_price: Decimal | None = None
    status_reason: str | None = None
    broker_response: dict | None = None
