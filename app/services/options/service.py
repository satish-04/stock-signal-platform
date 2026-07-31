from __future__ import annotations

from typing import Iterable

from app.services.brokers.base import BrokerAdapter
from app.services.options.models import OptionQuote


class OptionsService:
    def __init__(self, broker: BrokerAdapter) -> None:
        self.broker = broker

    async def chain(
        self,
        symbol: str,
    ) -> list[OptionQuote]:
        contracts = await self.broker.option_chain(symbol.upper())

        quotes: list[OptionQuote] = []

        for contract in contracts:
            quotes.append(
                OptionQuote(
                    symbol=contract.symbol,
                    expiry=contract.expiry,
                    strike=contract.strike,
                    option_type=(
                        "CALL"
                        if contract.right.upper() == "C"
                        else "PUT"
                    ),
                    bid=contract.bid,
                    ask=contract.ask,
                    last=(contract.bid + contract.ask) / 2,
                    volume=contract.volume,
                    open_interest=contract.open_interest,
                    implied_volatility=contract.implied_volatility,
                    delta=contract.delta,
                    gamma=contract.gamma,
                    theta=contract.theta,
                    vega=contract.vega,
                )
            )

        return quotes

    @staticmethod
    def filter_calls(
        quotes: Iterable[OptionQuote],
    ) -> list[OptionQuote]:
        return [
            q
            for q in quotes
            if q.option_type == "CALL"
        ]

    @staticmethod
    def filter_puts(
        quotes: Iterable[OptionQuote],
    ) -> list[OptionQuote]:
        return [
            q
            for q in quotes
            if q.option_type == "PUT"
        ]
