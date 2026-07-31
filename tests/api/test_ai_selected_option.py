from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_ai_recommendation_includes_selected_option() -> None:
    response = client.get("/api/v1/ai/recommendation/aapl")

    assert response.status_code == 200
    payload = response.json()

    assert payload["symbol"] == "AAPL"
    assert payload["action"] == "BUY_CALL"
    assert payload["selected_option"] is not None

    selected = payload["selected_option"]
    assert selected["symbol"] == "AAPL"
    assert selected["option_type"] == "CALL"
    assert selected["strike"] == "100"
    assert selected["expiry"] == "2026-09-18"
    assert selected["selection_score"] == 100.0
    assert isinstance(selected["selection_reasons"], list)


def test_ai_recommendation_selected_option_has_greeks() -> None:
    response = client.get("/api/v1/ai/recommendation/AAPL")

    assert response.status_code == 200
    selected = response.json()["selected_option"]

    assert selected["delta"] is not None
    assert selected["gamma"] is not None
    assert selected["theta"] is not None
    assert selected["vega"] is not None
    assert selected["implied_volatility"] is not None
