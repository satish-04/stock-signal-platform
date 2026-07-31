from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

ExitReason = Literal[
    "STOP_LOSS",
    "FIRST_TARGET",
    "SECOND_TARGET",
    "TRAILING_STOP",
    "MAX_HOLDING_TIME",
    "EXPIRATION_RISK",
    "STALE_MARK",
]
ExitSignalStatus = Literal[
    "CREATED",
    "APPROVED",
    "REJECTED",
    "INTENT_CREATED",
    "SUBMITTED",
    "COMPLETED",
    "FAILED",
]
ExitUrgency = Literal["NORMAL", "HIGH", "IMMEDIATE"]


@dataclass(frozen=True)
class PositionExitRules:
    stop_loss_pct: Decimal
    first_target_pct: Decimal
    second_target_pct: Decimal
    first_target_exit_pct: Decimal
    trailing_stop_enabled: bool
    trailing_activation_pct: Decimal
    trailing_distance_pct: Decimal
    max_holding_hours: int
    expiration_exit_days: int
    stale_mark_seconds: int


@dataclass(frozen=True)
class PositionExitContext:
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    quantity: int
    multiplier: int
    average_entry_price: Decimal
    current_mark_price: Decimal
    highest_mark_price: Decimal
    opened_at: datetime
    evaluated_at: datetime
    mark_updated_at: datetime
    expiration: datetime | None
    first_target_already_taken: bool


@dataclass(frozen=True)
class ExitEvaluation:
    triggered: bool
    reason: ExitReason | None
    urgency: ExitUrgency | None
    exit_quantity: int
    mark_price: Decimal
    trigger_price: Decimal | None
    price_return_pct: Decimal
    holding_hours: Decimal
    days_to_expiration: Decimal | None
    mark_age_seconds: Decimal
    explanations: tuple[str, ...]
    rejection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class PositionExitSignal:
    exit_signal_id: str
    idempotency_key: str
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    reason: ExitReason
    urgency: ExitUrgency
    status: ExitSignalStatus
    requested_quantity: int
    mark_price: Decimal
    trigger_price: Decimal | None
    created_at: datetime
    updated_at: datetime
    explanations: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
