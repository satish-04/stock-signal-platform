from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from app.core.config import Settings, get_settings

if TYPE_CHECKING:
    from app.services.positions.store import PositionStore

ZERO = Decimal(0)
# Accounts scanned per check; paper trading uses a handful.
MAX_ACCOUNTS = 1000


class EntryBlockedError(PermissionError):
    """Raised when a new position may not be opened."""


@dataclass(frozen=True)
class EntryGuardStatus:
    halted: bool
    trading_day: str
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    daily_loss: Decimal
    daily_loss_limit: Decimal

    @property
    def loss_locked(self) -> bool:
        return self.daily_loss >= self.daily_loss_limit

    @property
    def entries_allowed(self) -> bool:
        return not self.halted and not self.loss_locked


class EntryGuard:
    """Blocks opening orders when trading is halted or the daily loss limit is hit.

    Daily loss is today's realized P&L plus the unrealized P&L of open positions, across
    all paper accounts, measured against MAX_DAILY_LOSS_PCT of RISK_ACCOUNT_EQUITY.
    Closing orders are never blocked, so positions can still be exited.
    """

    def __init__(self, store: PositionStore, settings: Settings) -> None:
        self.store = store
        self.settings = settings

    async def status(self, now: datetime | None = None) -> EntryGuardStatus:
        from app.services.positions.service import trading_day

        day = trading_day(now or datetime.now(UTC))
        realized = unrealized = ZERO
        for account_id in await self.store.list_account_ids(limit=MAX_ACCOUNTS):
            realized += await self.store.get_realized_pnl(account_id, day)
            for position in await self.store.list_positions(account_id):
                if position.status == "OPEN" and position.unrealized_pnl is not None:
                    unrealized += position.unrealized_pnl
        limit = (
            Decimal(str(self.settings.risk_account_equity))
            * Decimal(str(self.settings.max_daily_loss_pct))
            / 100
        )
        return EntryGuardStatus(
            halted=self.settings.trading_halted,
            trading_day=day,
            realized_pnl=realized,
            unrealized_pnl=unrealized,
            daily_loss=max(ZERO, -(realized + unrealized)),
            daily_loss_limit=limit,
        )

    async def check(self, side: str, now: datetime | None = None) -> None:
        if side != "BUY":
            return
        if self.settings.trading_halted:
            raise EntryBlockedError("Trading is halted (TRADING_HALTED=true); only exits are allowed.")
        current = await self.status(now)
        if current.loss_locked:
            raise EntryBlockedError(
                f"Daily loss lock: loss {current.daily_loss:.2f} has reached the "
                f"{current.daily_loss_limit:.2f} limit; only exits are allowed until "
                "the next trading day."
            )


def default_entry_guard(settings: Settings) -> EntryGuard:
    # Imported here: the positions package imports the order-execution package.
    from app.services.positions.factory import get_position_store

    # The application settings share the cached store the positions API uses.
    shared = settings is get_settings()
    return EntryGuard(get_position_store(None if shared else settings), settings)
