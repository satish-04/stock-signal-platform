import pytest
from app.services.brokers.mock import MockBrokerAdapter
from app.services.options.engine import OptionsEngine

@pytest.mark.asyncio
async def test_bullish_defined_risk_strategy():
    chain = await MockBrokerAdapter().option_chain("AAPL")
    result = OptionsEngine().choose_defined_risk("bullish", chain)
    assert result["strategy"] == "call_debit_spread"
    assert result["max_loss"] > 0
