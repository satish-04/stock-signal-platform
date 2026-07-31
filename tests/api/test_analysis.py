from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_analysis_endpoint_returns_mock_indicators() -> None:
    response = client.get(
        "/api/v1/analysis/aapl",
        params={
            "duration": "5 D",
            "bar_size": "5 mins",
            "use_rth": "true",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["symbol"] == "AAPL"
    assert payload["duration"] == "5 D"
    assert payload["bar_size"] == "5 mins"
    assert payload["use_rth"] is True

    assert payload["ema_9"] is not None
    assert payload["ema_20"] is not None
    assert payload["ema_50"] is not None
    assert payload["ema_200"] is not None
    assert payload["sma_20"] is not None
    assert payload["rsi_14"] == 100.0
    assert payload["macd"] is not None
    assert payload["macd_signal"] is not None
    assert payload["macd_histogram"] is not None
    assert payload["atr_14"] is not None
    assert payload["vwap"] is not None
    assert payload["bollinger_upper"] is not None
    assert payload["bollinger_middle"] is not None
    assert payload["bollinger_lower"] is not None


def test_analysis_endpoint_normalizes_symbol() -> None:
    response = client.get("/api/v1/analysis/msft")

    assert response.status_code == 200
    assert response.json()["symbol"] == "MSFT"


def test_analysis_endpoint_validates_bar_size_length() -> None:
    response = client.get(
        "/api/v1/analysis/AAPL",
        params={"bar_size": "1"},
    )

    assert response.status_code == 422
