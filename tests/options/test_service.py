from decimal import Decimal

import pytest

from app.services.brokers.mock import MockBrokerAdapter
from app.services.options import OptionChainService


@pytest.mark.asyncio
async def test_option_chain_service_returns_chain() -> None:
    service = OptionChainService(MockBrokerAdapter())

    chain = await service.get_chain("AAPL")

    assert chain.symbol == "AAPL"
    assert chain.underlying_price == Decimal("100")
    assert len(chain.contracts) == 4


@pytest.mark.asyncio
async def test_option_contract_fields() -> None:
    service = OptionChainService(MockBrokerAdapter())

    chain = await service.get_chain("AAPL")

    contract = chain.contracts[0]

    assert contract.option_type == "CALL"
    assert contract.bid == Decimal("4.90")
    assert contract.ask == Decimal("5.10")
    assert contract.last == Decimal("5.00")
    assert contract.volume == 1500
    assert contract.open_interest == 6000
    assert contract.delta > 0


@pytest.mark.asyncio
async def test_put_contract() -> None:
    service = OptionChainService(MockBrokerAdapter())

    chain = await service.get_chain("AAPL")

    put = next(
        c for c in chain.contracts
        if c.option_type == "PUT"
    )

    assert put.delta < 0
    assert put.volume > 0


@pytest.mark.asyncio
async def test_symbol_is_normalized() -> None:
    service = OptionChainService(MockBrokerAdapter())

    chain = await service.get_chain("aapl")

    assert chain.symbol == "AAPL"


@pytest.mark.asyncio
async def test_blank_symbol_rejected() -> None:
    service = OptionChainService(MockBrokerAdapter())

    with pytest.raises(ValueError):
        await service.get_chain(" ")
