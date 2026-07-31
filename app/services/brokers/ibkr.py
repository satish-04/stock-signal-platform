"""IBKR adapter boundary.

Install the official TWS Python API and implement callbacks here. The application deliberately
fails closed until a tested implementation is supplied, preventing accidental live operation.
"""
from app.core.config import get_settings

class IBKRBrokerAdapter:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def stock_snapshot(self, symbol: str):
        raise NotImplementedError("Connect official IBKR TWS API callbacks before MARKET_DATA_MODE=ibkr")

    async def option_chain(self, symbol: str):
        raise NotImplementedError("Implement reqSecDefOptParams and reqMktData callbacks")

    async def submit_order(self, order: dict):
        if not self.settings.enable_order_submission:
            raise PermissionError("Order submission disabled")
        raise NotImplementedError("Implement bracket/combination order submission in paper account first")
