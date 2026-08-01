from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal


OptionType = Literal["CALL", "PUT"]


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    expiry: str
    strike: Decimal
    option_type: OptionType

    bid: Decimal
    ask: Decimal
    last: Decimal

    volume: int
    open_interest: int

    implied_volatility: float

    delta: float
    gamma: float
    theta: float
    vega: float


@dataclass(frozen=True)
class OptionContract:
    symbol: str
    expiration: date
    strike: Decimal
    option_type: OptionType

    bid: Decimal
    ask: Decimal
    last: Decimal

    volume: int
    open_interest: int

    implied_volatility: float

    delta: float
    gamma: float
    theta: float
    vega: float

    in_the_money: bool


@dataclass(frozen=True)
class OptionChain:
    symbol: str
    underlying_price: Decimal
    contracts: tuple[OptionContract, ...]
