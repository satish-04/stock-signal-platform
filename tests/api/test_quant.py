from fastapi.testclient import TestClient

from app.main import app
from app.services.quant import service

client = TestClient(app)


def test_quant_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "post" in paths["/api/v1/quant/backtest"]
    assert "get" in paths["/api/v1/quant/regime"]


def test_backtest_rejects_an_unknown_strategy() -> None:
    response = client.post("/api/v1/quant/backtest", json={"symbol": "SPY", "strategy": "martingale"})

    assert response.status_code == 422


def test_backtest_rejects_a_malformed_symbol() -> None:
    response = client.post("/api/v1/quant/backtest", json={"symbol": "SPY; DROP"})

    assert response.status_code == 422


def test_backtest_reports_missing_history(monkeypatch) -> None:
    async def nothing(*args, **kwargs):
        return None

    monkeypatch.setattr(service, "backtest", nothing)
    response = client.post("/api/v1/quant/backtest", json={"symbol": "zzzz"})

    assert response.status_code == 404
    assert "ZZZZ" in response.json()["detail"]


def test_backtest_reports_a_provider_failure_as_a_gateway_error(monkeypatch) -> None:
    async def broken(*args, **kwargs):
        raise RuntimeError("rate limited")

    monkeypatch.setattr(service, "backtest", broken)
    response = client.post("/api/v1/quant/backtest", json={"symbol": "SPY"})

    assert response.status_code == 502
