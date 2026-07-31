from dataclasses import replace
from datetime import UTC
from decimal import ROUND_HALF_UP, Decimal

from app.services.positions.models import ExecutionFill, Position, PositionUpdateResult

ZERO = Decimal(0)
CENT = Decimal("0.01")


class PositionAccountingError(RuntimeError):
    """Raised when a fill cannot be applied to a position."""


class PositionAccountingEngine:
    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_UP)

    @classmethod
    def _validate_fill(cls, fill: ExecutionFill) -> None:
        if not all(
            value.strip()
            for value in (fill.fill_id, fill.execution_id, fill.account_id, fill.symbol, fill.option_symbol)
        ):
            raise ValueError("Fill identifiers and symbols must not be empty.")
        if fill.quantity <= 0 or fill.fill_price <= ZERO or fill.multiplier <= 0:
            raise ValueError("Fill quantity, price, and multiplier must be positive.")
        if fill.filled_at.tzinfo is None:
            raise ValueError("filled_at must be timezone-aware.")

    @staticmethod
    def _validate_match(position: Position, fill: ExecutionFill) -> None:
        if (
            position.account_id != fill.account_id
            or position.option_symbol != fill.option_symbol
            or position.multiplier != fill.multiplier
        ):
            raise PositionAccountingError("Fill does not match the position.")

    @classmethod
    def open_position(cls, position_id: str, fill: ExecutionFill) -> PositionUpdateResult:
        cls._validate_fill(fill)
        if fill.side != "BUY":
            raise PositionAccountingError("A long position must be opened with a BUY fill.")
        timestamp = fill.filled_at.astimezone(UTC)
        price = cls._money(fill.fill_price)
        cost = cls._money(price * fill.quantity * fill.multiplier)
        position = Position(
            position_id=position_id,
            account_id=fill.account_id,
            symbol=fill.symbol.strip().upper(),
            option_symbol=fill.option_symbol.strip(),
            side="LONG",
            status="OPEN",
            quantity=fill.quantity,
            multiplier=fill.multiplier,
            average_entry_price=price,
            current_mark_price=None,
            cost_basis=cost,
            market_value=None,
            realized_pnl=Decimal("0.00"),
            unrealized_pnl=None,
            opened_at=timestamp,
            updated_at=timestamp,
            closed_at=None,
        )
        return PositionUpdateResult(
            position, fill.fill_id, fill.quantity, Decimal("0.00"), True, False, False, False
        )

    @classmethod
    def apply_fill(cls, position: Position, fill: ExecutionFill) -> PositionUpdateResult:
        cls._validate_fill(fill)
        cls._validate_match(position, fill)
        if position.status != "OPEN":
            raise PositionAccountingError("Closed positions cannot accept fills.")
        timestamp = fill.filled_at.astimezone(UTC)
        if fill.side == "BUY":
            quantity = position.quantity + fill.quantity
            average = cls._money(
                (
                    position.average_entry_price * position.quantity
                    + fill.fill_price * fill.quantity
                )
                / quantity
            )
            updated = replace(
                position,
                quantity=quantity,
                average_entry_price=average,
                cost_basis=cls._money(average * quantity * position.multiplier),
                current_mark_price=None,
                market_value=None,
                unrealized_pnl=None,
                updated_at=timestamp,
            )
            return PositionUpdateResult(
                updated, fill.fill_id, fill.quantity, Decimal("0.00"), False, True, False, False
            )
        if fill.quantity > position.quantity:
            raise PositionAccountingError("Sell fill exceeds the open position quantity.")
        remaining = position.quantity - fill.quantity
        realized_change = cls._money(
            (fill.fill_price - position.average_entry_price)
            * fill.quantity
            * position.multiplier
        )
        closed = remaining == 0
        updated = replace(
            position,
            status="CLOSED" if closed else "OPEN",
            quantity=remaining,
            cost_basis=cls._money(
                position.average_entry_price * remaining * position.multiplier
            ),
            realized_pnl=cls._money(position.realized_pnl + realized_change),
            current_mark_price=None if closed else position.current_mark_price,
            market_value=Decimal("0.00") if closed else position.market_value,
            unrealized_pnl=Decimal("0.00") if closed else position.unrealized_pnl,
            updated_at=timestamp,
            closed_at=timestamp if closed else None,
        )
        return PositionUpdateResult(
            updated, fill.fill_id, -fill.quantity, realized_change, False, False, True, closed
        )

    @classmethod
    def mark(cls, position: Position, mark_price: Decimal) -> Position:
        if position.status != "OPEN":
            raise PositionAccountingError("Only open positions can be marked.")
        if mark_price <= ZERO:
            raise ValueError("mark_price must be positive.")
        mark = cls._money(mark_price)
        market_value = cls._money(mark * position.quantity * position.multiplier)
        return replace(
            position,
            current_mark_price=mark,
            market_value=market_value,
            unrealized_pnl=cls._money(market_value - position.cost_basis),
        )
