from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.services.brokers.base import HistoricalBar
from app.services.brokers.ibkr_historical import IBKRHistoricalClient


class IBKRBrokerAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def stock_snapshot(self, symbol: str):
        raise NotImplementedError(
            "Live IBKR stock snapshots require market-data subscriptions."
        )

    async def historical_bars(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> list[HistoricalBar]:
        client = IBKRHistoricalClient(
            host=self.settings.ibkr_host,
            port=self.settings.ibkr_port,
            client_id=self.settings.ibkr_client_id,
        )

        ibkr_bars = await asyncio.to_thread(
            client.fetch,
            symbol,
            duration,
            bar_size,
            use_rth,
        )

        return [
            HistoricalBar(
                symbol=symbol.upper(),
                timestamp=bar.timestamp,
                open=bar.open,
                high=bar.high,
                low=bar.low,
                close=bar.close,
                volume=bar.volume,
            )
            for bar in ibkr_bars
        ]

    async def option_chain(self, symbol: str):
        raise NotImplementedError(
            "Implement reqSecDefOptParams and option market-data callbacks."
        )

    async def submit_order(self, order: dict):
        if not self.settings.enable_order_submission:
            raise PermissionError("Order submission disabled.")

        raise NotImplementedError(
            "Implement paper combination-order submission first."
        )
