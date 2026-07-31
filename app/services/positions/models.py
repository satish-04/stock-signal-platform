from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal

PositionStatus = Literal["OPEN", "CLOSED"]
PositionSide = Literal["LONG", "SHORT"]
FillSide = Literal["BUY", "SELL"]


@dataclass(frozen=True)
class ExecutionFill:
    fill_id: str
    execution_id: str
    broker_order_id: str | None
    account_id: str
    symbol: str
    option_symbol: str
    side: FillSide
    quantity: int
    fill_price: Decimal
    multiplier: int
    filled_at: datetime


@dataclass(frozen=True)
class Position:
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    side: PositionSide
    status: PositionStatus
    quantity: int
    multiplier: int
    average_entry_price: Decimal
    current_mark_price: Decimal | None
    cost_basis: Decimal
    market_value: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal | None
    opened_at: datetime
    updated_at: datetime
    closed_at: datetime | None


@dataclass(frozen=True)
class PositionUpdateResult:
    position: Position
    processed_fill_id: str
    quantity_change: int
    realized_pnl_change: Decimal
    opened: bool
    increased: bool
    reduced: bool
    closed: bool
