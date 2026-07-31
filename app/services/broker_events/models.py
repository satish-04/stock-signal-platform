from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

BrokerEventType = Literal[
    "ORDER_STATUS", "OPEN_ORDER", "EXECUTION_DETAILS", "COMMISSION_REPORT", "BROKER_ERROR"
]
BrokerEventStatus = Literal[
    "RECEIVED", "PROCESSING", "PROCESSED", "SKIPPED", "FAILED", "DEAD_LETTER"
]
NormalizedOrderStatus = Literal[
    "PENDING_SUBMIT", "PENDING_CANCEL", "PRE_SUBMITTED", "SUBMITTED",
    "API_CANCELLED", "CANCELLED", "FILLED", "INACTIVE", "UNKNOWN",
]


@dataclass(frozen=True)
class BrokerOrderStatusPayload:
    broker_order_id: str
    broker_status: str
    normalized_status: NormalizedOrderStatus
    filled_quantity: Decimal
    remaining_quantity: Decimal
    average_fill_price: Decimal | None
    permanent_id: str | None
    parent_order_id: str | None
    last_fill_price: Decimal | None
    client_id: int | None
    why_held: str | None
    market_cap_price: Decimal | None


@dataclass(frozen=True)
class BrokerExecutionPayload:
    broker_order_id: str
    execution_id: str
    account_id: str
    symbol: str
    option_symbol: str
    side: Literal["BUY", "SELL"]
    quantity: Decimal
    fill_price: Decimal
    cumulative_quantity: Decimal
    average_price: Decimal
    exchange: str | None
    execution_time: datetime
    permanent_id: str | None
    client_id: int | None


@dataclass(frozen=True)
class BrokerCommissionPayload:
    execution_id: str
    commission: Decimal
    currency: str
    realized_pnl: Decimal | None
    yield_value: Decimal | None
    yield_redemption_date: int | None


@dataclass(frozen=True)
class BrokerErrorPayload:
    request_id: str | None
    error_code: int
    error_message: str
    advanced_order_reject_json: str | None


BrokerEventPayload = (
    BrokerOrderStatusPayload | BrokerExecutionPayload | BrokerCommissionPayload | BrokerErrorPayload
)


@dataclass(frozen=True)
class BrokerEvent:
    event_id: str
    idempotency_key: str
    event_type: BrokerEventType
    status: BrokerEventStatus
    broker: Literal["IBKR"]
    trading_mode: Literal["paper"]
    broker_order_id: str | None
    execution_id: str | None
    payload: BrokerEventPayload
    attempt_count: int
    max_attempts: int
    received_at: datetime
    processing_started_at: datetime | None
    processed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    error_type: str | None
    error_message: str | None
    retryable: bool


@dataclass(frozen=True)
class BrokerEventProcessingResult:
    event: BrokerEvent
    execution_id: str | None
    execution_status: str | None
    position_reconciliation_required: bool
    message: str
