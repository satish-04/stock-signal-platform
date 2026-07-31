from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.services.brokers.base import (
    HistoricalBar,
    OptionContractSnapshot,
    StockSnapshot,
)


class MockBrokerAdapter:
    async def stock_snapshot(self, symbol: str) -> StockSnapshot:
        return StockSnapshot(
            symbol=symbol.upper(),
            bid=Decimal("99.95"),
            ask=Decimal("100.05"),
            last=Decimal("100.00"),
            volume=1_000_000,
        )

    async def historical_bars(
        self,
        symbol: str,
        duration: str = "1 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> list[HistoricalBar]:
        del duration, bar_size, use_rth

        normalized_symbol = symbol.upper()
        start = datetime(
            2026,
            1,
            2,
            14,
            30,
            tzinfo=timezone.utc,
        )

        bars: list[HistoricalBar] = []

        for index in range(220):
            close = Decimal("100.00") + (
                Decimal(index) * Decimal("0.10")
            )

            bars.append(
                HistoricalBar(
                    symbol=normalized_symbol,
                    timestamp=start + timedelta(minutes=5 * index),
                    open=close - Decimal("0.05"),
                    high=close + Decimal("0.20"),
                    low=close - Decimal("0.20"),
                    close=close,
                    volume=100_000 + (index * 1_000),
                )
            )

        return bars

    async def option_chain(
        self,
        symbol: str,
    ) -> list[OptionContractSnapshot]:
        normalized_symbol = symbol.upper()

        return [
            OptionContractSnapshot(
                1,
                normalized_symbol,
                "2026-09-18",
                Decimal("100"),
                "C",
                Decimal("4.90"),
                Decimal("5.10"),
                1500,
                6000,
                0.32,
                0.55,
                0.04,
                -0.08,
                0.12,
            ),
            OptionContractSnapshot(
                2,
                normalized_symbol,
                "2026-09-18",
                Decimal("105"),
                "C",
                Decimal("2.40"),
                Decimal("2.55"),
                1200,
                5200,
                0.31,
                0.38,
                0.035,
                -0.065,
                0.10,
            ),
            OptionContractSnapshot(
                3,
                normalized_symbol,
                "2026-09-18",
                Decimal("100"),
                "P",
                Decimal("4.70"),
                Decimal("4.90"),
                1400,
                5800,
                0.33,
                -0.45,
                0.04,
                -0.08,
                0.12,
            ),
            OptionContractSnapshot(
                4,
                normalized_symbol,
                "2026-09-18",
                Decimal("95"),
                "P",
                Decimal("2.20"),
                Decimal("2.35"),
                1100,
                5000,
                0.32,
                -0.30,
                0.03,
                -0.06,
                0.09,
            ),
        ]

    async def submit_order(self, order: dict) -> dict:
        return {
            "status": "simulated",
            "order": order,
        }
