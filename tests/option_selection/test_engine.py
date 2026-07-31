from __future__ import annotations

import pytest

from app.services.brokers.mock import MockBrokerAdapter
from app.services.option_selection import OptionSelectionEngine
from app.services.options.service import OptionsService


@pytest.mark.asyncio
async def test_rank_returns_sorted_options() -> None:
    service = OptionsService(MockBrokerAdapter())
    quotes = await service.chain("AAPL")

    ranked = OptionSelectionEngine.rank(quotes)

    assert len(ranked) == 4

    for i in range(len(ranked) - 1):
        assert ranked[i].score >= ranked[i + 1].score


@pytest.mark.asyncio
async def test_filter_calls() -> None:
    service = OptionsService(MockBrokerAdapter())
    quotes = await service.chain("AAPL")

    ranked = OptionSelectionEngine.rank(
        quotes,
        option_type="CALL",
    )

    assert len(ranked) == 2

    assert all(
        item.quote.option_type == "CALL"
        for item in ranked
    )


@pytest.mark.asyncio
async def test_filter_puts() -> None:
    service = OptionsService(MockBrokerAdapter())
    quotes = await service.chain("AAPL")

    ranked = OptionSelectionEngine.rank(
        quotes,
        option_type="PUT",
    )

    assert len(ranked) == 2

    assert all(
        item.quote.option_type == "PUT"
        for item in ranked
    )


@pytest.mark.asyncio
async def test_limit_results() -> None:
    service = OptionsService(MockBrokerAdapter())
    quotes = await service.chain("AAPL")

    ranked = OptionSelectionEngine.rank(
        quotes,
        limit=1,
    )

    assert len(ranked) == 1


def test_invalid_option_type() -> None:
    with pytest.raises(ValueError):
        OptionSelectionEngine.rank(
            [],
            option_type="INVALID",
        )


def test_invalid_limit() -> None:
    with pytest.raises(ValueError):
        OptionSelectionEngine.rank(
            [],
            limit=0,
        )
