from __future__ import annotations

from app.services.brokers.base import BrokerAdapter
from app.services.indicators.engine import IndicatorEngine
from app.services.indicators.models import Candle, IndicatorResult


class IndicatorService:
    def __init__(self, broker: BrokerAdapter) -> None:
        self.broker = broker

    async def calculate_for_symbol(
        self,
        symbol: str,
        duration: str = "5 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> IndicatorResult:
        bars = await self.broker.historical_bars(
            symbol=symbol,
            duration=duration,
            bar_size=bar_size,
            use_rth=use_rth,
        )

        if not bars:
            raise ValueError(
                f"No historical bars returned for symbol {symbol.upper()}."
            )

        candles = [
            Candle(
                timestamp=bar.timestamp,
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
            )
            for bar in bars
        ]

        return IndicatorEngine.calculate(candles)
