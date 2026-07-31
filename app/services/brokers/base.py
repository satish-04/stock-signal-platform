from dataclasses import dataclass
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
    async def stock_snapshot(self, symbol: str) -> StockSnapshot: ...
    async def option_chain(self, symbol: str) -> list[OptionContractSnapshot]: ...
    async def submit_order(self, order: dict) -> dict: ...
