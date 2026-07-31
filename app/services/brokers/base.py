from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class StockSnapshot:
    symbol: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int


@dataclass(frozen=True)
class HistoricalBar:
    symbol: str
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int


@dataclass(frozen=True)
class OptionContractSnapshot:
    conid: int
    symbol: str
    expiry: str
    strike: Decimal
    right: str
    bid: Decimal
    ask: Decimal
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float


class BrokerAdapter(Protocol):
    async def stock_snapshot(
        self,
        symbol: str,
    ) -> StockSnapshot: ...

    async def historical_bars(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> list[HistoricalBar]: ...

    async def option_chain(
        self,
        symbol: str,
    ) -> list[OptionContractSnapshot]: ...

    async def submit_order(
        self,
        order: dict,
    ) -> dict: ...

    async def cancel_order(self, order: dict) -> dict: ...
