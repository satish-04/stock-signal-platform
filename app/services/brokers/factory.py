from app.core.config import get_settings
from app.services.brokers.mock import MockBrokerAdapter

def get_broker():
    settings = get_settings()
    if settings.market_data_mode == "mock":
        return MockBrokerAdapter()
    from app.services.brokers.ibkr import IBKRBrokerAdapter
    return IBKRBrokerAdapter()
