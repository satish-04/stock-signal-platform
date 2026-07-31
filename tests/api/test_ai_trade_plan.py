from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_recommendation_serializes_trade_plan() -> None:
    response = client.get("/api/v1/ai/recommendation/AAPL")
    assert response.status_code == 200
    payload = response.json()
    assert payload["selected_option"] is not None
    plan = payload["trade_plan"]
    assert plan is not None
    assert plan["decision"] in {"APPROVED", "REJECTED"}
    assert plan["side"] == "BUY"
    assert plan["order_type"] == "LIMIT"
    assert isinstance(plan["quantity"], int)
    assert isinstance(plan["reasons"], list)
    assert isinstance(plan["rejection_reasons"], list)


def test_ai_trade_plan_matches_selected_contract() -> None:
    response = client.get("/api/v1/ai/recommendation/aapl")
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "BUY_CALL"
    assert payload["selected_option"]["option_type"] == "CALL"
    assert payload["trade_plan"]["quantity"] >= 0
    assert payload["trade_plan"]["maximum_loss"] == payload["trade_plan"][
        "estimated_debit"
    ]
