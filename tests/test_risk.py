from app.services.risk.engine import RiskEngine

def test_rejects_oversized_trade():
    result = RiskEngine().evaluate({"strategy": "call_debit_spread", "max_loss": 1000}, account_equity=10000)
    assert not result.approved
