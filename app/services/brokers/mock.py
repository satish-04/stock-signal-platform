from decimal import Decimal
from app.services.brokers.base import OptionContractSnapshot, StockSnapshot

class MockBrokerAdapter:
    async def stock_snapshot(self, symbol: str) -> StockSnapshot:
        return StockSnapshot(symbol=symbol, bid=Decimal("99.95"), ask=Decimal("100.05"), last=Decimal("100"), volume=1000000)

    async def option_chain(self, symbol: str) -> list[OptionContractSnapshot]:
        return [
            OptionContractSnapshot(1, symbol, "2026-09-18", Decimal("100"), "C", Decimal("4.90"), Decimal("5.10"), 1500, 6000, 0.32, 0.55, 0.04, -0.08, 0.12),
            OptionContractSnapshot(2, symbol, "2026-09-18", Decimal("105"), "C", Decimal("2.40"), Decimal("2.55"), 1200, 5200, 0.31, 0.38, 0.035, -0.065, 0.10),
            OptionContractSnapshot(3, symbol, "2026-09-18", Decimal("100"), "P", Decimal("4.70"), Decimal("4.90"), 1400, 5800, 0.33, -0.45, 0.04, -0.08, 0.12),
            OptionContractSnapshot(4, symbol, "2026-09-18", Decimal("95"), "P", Decimal("2.20"), Decimal("2.35"), 1100, 5000, 0.32, -0.30, 0.03, -0.06, 0.09),
        ]

    async def submit_order(self, order: dict) -> dict:
        return {"status": "simulated", "order": order}
