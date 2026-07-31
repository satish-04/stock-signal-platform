from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_technical_signal_endpoint_returns_signal() -> None:
    response = client.get(
        "/api/v1/signals/technical/aapl",
        params={
            "duration": "5 D",
            "bar_size": "5 mins",
            "use_rth": "true",
        },
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["symbol"] == "AAPL"
    assert payload["direction"] in {
        "bullish",
        "bearish",
        "neutral",
    }
    assert 0.0 <= payload["confidence"] <= 100.0
    assert isinstance(payload["trend_score"], float)
    assert isinstance(payload["momentum_score"], float)
    assert isinstance(payload["volatility_score"], float)
    assert isinstance(payload["volume_score"], float)
    assert isinstance(payload["reasons"], list)
    assert isinstance(payload["warnings"], list)


def test_technical_signal_endpoint_normalizes_symbol() -> None:
    response = client.get(
        "/api/v1/signals/technical/msft"
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "MSFT"


def test_technical_signal_endpoint_supports_rth_false() -> None:
    response = client.get(
        "/api/v1/signals/technical/AAPL",
        params={"use_rth": "false"},
    )

    assert response.status_code == 200
