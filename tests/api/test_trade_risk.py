from __future__ import annotations

from copy import deepcopy

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def approved_payload() -> dict:
    return {
        "symbol": "aapl",
        "option_symbol": "AAPL  260918C00100000",
        "option_type": "CALL",
        "expiry": "2026-09-18",
        "strike": "100",
        "multiplier": 100,
        "bid": "4.90",
        "ask": "5.10",
        "last": "5.00",
        "volume": 1500,
        "open_interest": 6000,
        "action": "BUY_CALL",
        "confidence": "90",
        "stop_loss_pct": "20",
        "first_target_pct": "40",
        "second_target_pct": "80",
        "limits": {
            "account_equity": "100000",
            "available_funds": "50000",
            "max_risk_per_trade_pct": "1.00",
            "max_position_value_pct": "2.00",
            "max_contracts": 5,
            "max_bid_ask_spread_pct": "5.00",
            "minimum_open_interest": 1000,
            "minimum_volume": 250,
            "minimum_reward_risk_ratio": "2.00",
        },
    }


def test_trade_plan_endpoint_approves_valid_trade() -> None:
    response = client.post("/api/v1/risk/trade-plan", json=approved_payload())
    assert response.status_code == 200
    payload = response.json()
    assert payload["symbol"] == "AAPL"
    assert payload["decision"] == "APPROVED"
    assert payload["quantity"] == 2
    assert payload["limit_price"] == "5.00"
    assert payload["maximum_loss"] == "1000.00"
    assert payload["reward_risk_ratio"] == "2.00"
    assert payload["rejection_reasons"] == []


def test_trade_plan_endpoint_returns_rejected_plan() -> None:
    payload = approved_payload()
    payload.update(volume=10, open_interest=50, bid="4.00", ask="6.00")
    response = client.post("/api/v1/risk/trade-plan", json=payload)
    assert response.status_code == 200
    result = response.json()
    assert result["decision"] == "REJECTED"
    assert len(result["rejection_reasons"]) >= 3


def test_trade_plan_endpoint_rejects_action_contract_mismatch() -> None:
    payload = approved_payload()
    payload["option_type"] = "PUT"
    response = client.post("/api/v1/risk/trade-plan", json=payload)
    assert response.status_code == 200
    assert response.json()["decision"] == "REJECTED"


def test_trade_plan_endpoint_returns_422_for_invalid_payload() -> None:
    payload = approved_payload()
    payload["ask"] = "0"
    response = client.post("/api/v1/risk/trade-plan", json=payload)
    assert response.status_code == 422


def test_trade_plan_endpoint_returns_422_for_invalid_target_order() -> None:
    payload = deepcopy(approved_payload())
    payload["first_target_pct"] = "40"
    payload["second_target_pct"] = "20"
    response = client.post("/api/v1/risk/trade-plan", json=payload)
    assert response.status_code == 422
    assert "second_target_pct must be greater" in response.json()["detail"]
