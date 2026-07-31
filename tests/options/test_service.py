from __future__ import annotations

import pytest

from app.services.brokers.mock import MockBrokerAdapter
from app.services.options.service import OptionsService


@pytest.mark.asyncio
async def test_option_chain_returns_quotes() -> None:
    service = OptionsService(MockBrokerAdapter())

    quotes = await service.chain("AAPL")

    assert len(quotes) == 4
    assert quotes[0].symbol == "AAPL"


@pytest.mark.asyncio
async def test_filter_calls() -> None:
    service = OptionsService(MockBrokerAdapter())

    quotes = await service.chain("AAPL")

    calls = service.filter_calls(quotes)

    assert len(calls) == 2

    assert all(
        q.option_type == "CALL"
        for q in calls
    )


@pytest.mark.asyncio
async def test_filter_puts() -> None:
    service = OptionsService(MockBrokerAdapter())

    quotes = await service.chain("AAPL")

    puts = service.filter_puts(quotes)

    assert len(puts) == 2

    assert all(
        q.option_type == "PUT"
        for q in puts
    )
