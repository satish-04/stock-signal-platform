from __future__ import annotations

import asyncio

from app.core.config import get_settings
from app.services.brokers.base import (
    HistoricalBar,
    OptionContractSnapshot,
)
from app.services.brokers.ibkr_historical import IBKRHistoricalClient
from app.services.brokers.ibkr_options import IBKROptionsClient


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

    async def option_chain(
        self,
        symbol: str,
    ) -> list[OptionContractSnapshot]:
        client = IBKROptionsClient(
            host=self.settings.ibkr_host,
            port=self.settings.ibkr_port,
            client_id=self.settings.ibkr_client_id,
        )

        snapshots = await asyncio.to_thread(
            client.fetch_chain,
            symbol,
        )

        return [
            OptionContractSnapshot(
                conid=snapshot.conid,
                symbol=snapshot.symbol,
                expiry=snapshot.expiry,
                strike=snapshot.strike,
                right=snapshot.right,
                bid=snapshot.bid,
                ask=snapshot.ask,
                volume=snapshot.volume,
                open_interest=snapshot.open_interest,
                implied_volatility=snapshot.implied_volatility,
                delta=snapshot.delta,
                gamma=snapshot.gamma,
                theta=snapshot.theta,
                vega=snapshot.vega,
            )
            for snapshot in snapshots
        ]

    async def submit_order(self, order: dict):
        if not self.settings.enable_order_submission:
            raise PermissionError("Order submission disabled.")

        raise NotImplementedError(
            "Implement paper combination-order submission first."
        )

    async def cancel_order(self, order: dict):
        if not self.settings.enable_order_submission:
            raise PermissionError("Order submission disabled.")
        raise NotImplementedError(
            "Implement IBKR paper-order cancellation callbacks first."
        )
