from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_historical_endpoint_returns_mock_bars() -> None:
    response = client.get(
        "/api/v1/historical/aapl",
        params={
            "duration": "1 D",
            "bar_size": "5 mins",
            "use_rth": "true",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["symbol"] == "AAPL"
    assert payload["duration"] == "1 D"
    assert payload["bar_size"] == "5 mins"
    assert payload["use_rth"] is True
    assert payload["count"] == 220
    assert len(payload["bars"]) == 220

    first_bar = payload["bars"][0]

    assert first_bar["symbol"] == "AAPL"
    assert first_bar["open"] == "99.95"
    assert first_bar["high"] == "100.20"
    assert first_bar["low"] == "99.80"
    assert first_bar["close"] == "100.00"
    assert first_bar["volume"] == 100000


def test_historical_endpoint_normalizes_symbol() -> None:
    response = client.get("/api/v1/historical/msft")

    assert response.status_code == 200
    assert response.json()["symbol"] == "MSFT"


def test_historical_endpoint_validates_duration_length() -> None:
    response = client.get(
        "/api/v1/historical/AAPL",
        params={"duration": "1"},
    )

    assert response.status_code == 422
