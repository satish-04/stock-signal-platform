from decimal import Decimal

import pytest

from app.services.brokers.base import HistoricalBar
from app.services.brokers.mock import MockBrokerAdapter
from app.services.indicators.service import IndicatorService


@pytest.mark.asyncio
async def test_indicator_service_calculates_from_broker_bars() -> None:
    service = IndicatorService(MockBrokerAdapter())

    result = await service.calculate_for_symbol("aapl")

    assert result.ema_9 is not None
    assert result.ema_20 is not None
    assert result.ema_50 is not None
    assert result.ema_200 is not None
    assert result.rsi_14 == pytest.approx(100.0)
    assert result.macd is not None
    assert result.atr_14 is not None
    assert result.vwap is not None


@pytest.mark.asyncio
async def test_indicator_service_passes_request_parameters() -> None:
    class RecordingBroker:
        def __init__(self) -> None:
            self.request: dict | None = None

        async def historical_bars(
            self,
            symbol: str,
            duration: str = "1 D",
            bar_size: str = "5 mins",
            use_rth: bool = True,
        ) -> list[HistoricalBar]:
            self.request = {
                "symbol": symbol,
                "duration": duration,
                "bar_size": bar_size,
                "use_rth": use_rth,
            }

            return await MockBrokerAdapter().historical_bars(symbol)

    broker = RecordingBroker()
    service = IndicatorService(broker)

    await service.calculate_for_symbol(
        symbol="MSFT",
        duration="10 D",
        bar_size="15 mins",
        use_rth=False,
    )

    assert broker.request == {
        "symbol": "MSFT",
        "duration": "10 D",
        "bar_size": "15 mins",
        "use_rth": False,
    }


@pytest.mark.asyncio
async def test_indicator_service_rejects_empty_bars() -> None:
    class EmptyBroker:
        async def historical_bars(
            self,
            symbol: str,
            duration: str = "1 D",
            bar_size: str = "5 mins",
            use_rth: bool = True,
        ) -> list[HistoricalBar]:
            return []

    service = IndicatorService(EmptyBroker())

    with pytest.raises(
        ValueError,
        match="No historical bars returned for symbol AAPL",
    ):
        await service.calculate_for_symbol("aapl")
