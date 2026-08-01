from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.services.brokers.base import BrokerAdapter
from app.services.options.models import (
    OptionChain,
    OptionContract,
    OptionQuote,
)


class OptionsService:
    """Existing normalized option-quote service."""

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
                    last=(contract.bid + contract.ask) / Decimal("2"),
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


class OptionChainService:
    """Extended option-chain representation including underlying price."""

    def __init__(self, broker: BrokerAdapter) -> None:
        self.broker = broker

    async def get_chain(
        self,
        symbol: str,
    ) -> OptionChain:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("Symbol must not be empty.")

        snapshot = await self.broker.stock_snapshot(
            normalized_symbol
        )

        broker_contracts = await self.broker.option_chain(
            normalized_symbol
        )

        contracts: list[OptionContract] = []

        for contract in broker_contracts:
            expiration = datetime.strptime(
                contract.expiry,
                "%Y-%m-%d",
            ).date()

            option_type = (
                "CALL"
                if contract.right.upper() == "C"
                else "PUT"
            )

            strike = Decimal(contract.strike)
            underlying_price = Decimal(snapshot.last)

            in_the_money = (
                strike < underlying_price
                if option_type == "CALL"
                else strike > underlying_price
            )

            contracts.append(
                OptionContract(
                    symbol=normalized_symbol,
                    expiration=expiration,
                    strike=strike,
                    option_type=option_type,
                    bid=contract.bid,
                    ask=contract.ask,
                    last=(
                        contract.bid + contract.ask
                    ) / Decimal("2"),
                    volume=contract.volume,
                    open_interest=contract.open_interest,
                    implied_volatility=contract.implied_volatility,
                    delta=contract.delta,
                    gamma=contract.gamma,
                    theta=contract.theta,
                    vega=contract.vega,
                    in_the_money=in_the_money,
                )
            )

        return OptionChain(
            symbol=normalized_symbol,
            underlying_price=Decimal(snapshot.last),
            contracts=tuple(contracts),
        )
