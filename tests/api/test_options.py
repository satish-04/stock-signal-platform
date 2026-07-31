from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_best_options_returns_ranked_call_and_put() -> None:
    response = client.get("/api/v1/options/best/aapl")

    assert response.status_code == 200
    payload = response.json()

    assert payload["symbol"] == "AAPL"
    assert payload["generated_at"].endswith("Z")

    best_call = payload["best_call"]
    assert best_call["symbol"] == "AAPL"
    assert best_call["option_type"] == "CALL"
    assert best_call["score"] == 100.0
    assert best_call["strike"] == "100"
    assert best_call["reasons"]

    best_put = payload["best_put"]
    assert best_put["symbol"] == "AAPL"
    assert best_put["option_type"] == "PUT"
    assert best_put["score"] == 100.0
    assert best_put["strike"] == "100"
    assert best_put["reasons"]


def test_best_options_normalizes_symbol() -> None:
    response = client.get("/api/v1/options/best/msft")

    assert response.status_code == 200
    payload = response.json()

    assert payload["symbol"] == "MSFT"
    assert payload["best_call"]["symbol"] == "MSFT"
    assert payload["best_put"]["symbol"] == "MSFT"
