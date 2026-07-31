import hashlib
from decimal import Decimal

from app.core.config import Settings, get_settings
from app.services.order_execution import OrderExecution
from app.services.positions.accounting import PositionAccountingEngine, PositionAccountingError
from app.services.positions.models import ExecutionFill, Position, PositionUpdateResult
from app.services.positions.store import PositionNotFoundError, PositionStore


class PositionExecutionError(RuntimeError):
    """Raised when a fill is inconsistent with its execution."""


class PaperPositionService:
    def __init__(self, store: PositionStore, settings: Settings | None = None) -> None:
        self.store = store
        self.settings = settings or get_settings()

    @staticmethod
    def _position_id(fill: ExecutionFill) -> str:
        digest = hashlib.sha256(
            f"{fill.account_id}|{fill.option_symbol}|LONG".encode()
        ).hexdigest()
        return f"position_{digest[:24]}"

    def _validate_execution(self, fill: ExecutionFill, execution: OrderExecution) -> None:
        if self.settings.trading_mode != "paper":
            raise PositionExecutionError("Position reconciliation is restricted to paper mode.")
        if execution.status not in {"PARTIALLY_FILLED", "FILLED"}:
            raise PositionExecutionError("Only filled executions can update positions.")
        if fill.execution_id != execution.execution_id:
            raise PositionExecutionError("Fill execution ID does not match execution.")
        if fill.option_symbol != execution.option_symbol or fill.side != execution.side:
            raise PositionExecutionError("Fill contract or side does not match execution.")
        if fill.broker_order_id != execution.broker_order_id:
            raise PositionExecutionError("Fill broker order ID does not match execution.")

    async def process_fill(
        self, fill: ExecutionFill, execution: OrderExecution
    ) -> PositionUpdateResult:
        self._validate_execution(fill, execution)
        await self.store.reserve_fill(fill.fill_id)
        try:
            position = await self.store.get_by_contract(
                fill.account_id, fill.option_symbol, "LONG"
            )
            if position is None:
                result = PositionAccountingEngine.open_position(
                    self._position_id(fill), fill
                )
            else:
                result = PositionAccountingEngine.apply_fill(position, fill)
            await self.store.save_update(result.position, fill)
            return result
        except (PositionAccountingError, ValueError, RuntimeError):
            await self.store.release_fill(fill.fill_id)
            raise

    async def get(self, position_id: str) -> Position:
        position = await self.store.get_position(position_id)
        if position is None:
            raise PositionNotFoundError(f"Position {position_id!r} was not found.")
        return position

    async def list_positions(
        self, account_id: str, *, status: str | None = None
    ) -> list[Position]:
        positions = await self.store.list_positions(account_id)
        if status:
            positions = [position for position in positions if position.status == status]
        return sorted(positions, key=lambda position: position.position_id)

    async def get_by_contract(self, account_id: str, option_symbol: str) -> Position:
        position = await self.store.get_by_contract(account_id, option_symbol, "LONG")
        if position is None:
            raise PositionNotFoundError("No position exists for the supplied contract.")
        return position

    async def update_mark(self, position_id: str, mark_price: Decimal) -> Position:
        position = PositionAccountingEngine.mark(await self.get(position_id), mark_price)
        await self.store.save_position(position)
        return position

    async def portfolio_summary(self, account_id: str) -> dict[str, Decimal | int]:
        positions = await self.list_positions(account_id)
        open_positions = [position for position in positions if position.status == "OPEN"]
        return {
            "total_positions": len(positions),
            "open_positions": len(open_positions),
            "closed_positions": len(positions) - len(open_positions),
            "total_cost_basis": sum(
                (position.cost_basis for position in open_positions), Decimal(0)
            ),
            "total_market_value": sum(
                (position.market_value or Decimal(0) for position in open_positions),
                Decimal(0),
            ),
            "realized_pnl": sum(
                (position.realized_pnl for position in positions), Decimal(0)
            ),
            "unrealized_pnl": sum(
                (position.unrealized_pnl or Decimal(0) for position in open_positions),
                Decimal(0),
            ),
        }
