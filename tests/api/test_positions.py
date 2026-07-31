from datetime import UTC, datetime
from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.routes import positions as route
from app.main import app
from app.services.positions import Position, PositionNotFoundError

client = TestClient(app)


def position() -> Position:
    now = datetime.now(UTC)
    return Position(
        "position-1", "paper", "AAPL", "AAPL-CALL", "LONG", "OPEN", 1, 100,
        Decimal(5), Decimal(6), Decimal(500), Decimal(600), Decimal(0),
        Decimal(100), now, now, None,
    )


class FakeService:
    async def get(self, position_id: str) -> Position:
        if position_id == "missing":
            raise PositionNotFoundError("not found")
        return position()

    async def get_by_contract(self, account_id: str, option_symbol: str) -> Position:
        return position()

    async def list_positions(self, account_id: str, *, status=None) -> list[Position]:
        return [position()]

    async def update_mark(self, position_id: str, mark_price: Decimal) -> Position:
        return position()

    async def portfolio_summary(self, account_id: str) -> dict:
        return {
            "open_positions": 1,
            "closed_positions": 0,
            "total_positions": 1,
            "total_cost_basis": Decimal(500),
            "total_market_value": Decimal(600),
            "realized_pnl": Decimal(0),
            "unrealized_pnl": Decimal(100),
        }


def test_list_and_get_position(monkeypatch) -> None:
    monkeypatch.setattr(route, "get_position_service", lambda: FakeService())
    listed = client.get("/api/v1/positions", params={"account_id": "paper"})
    assert listed.status_code == 200
    assert listed.json()["count"] == 1
    fetched = client.get("/api/v1/positions/position-1")
    assert fetched.status_code == 200
    assert fetched.json()["unrealized_pnl"] == "100"


def test_missing_position_returns_404(monkeypatch) -> None:
    monkeypatch.setattr(route, "get_position_service", lambda: FakeService())
    assert client.get("/api/v1/positions/missing").status_code == 404


def test_portfolio_summary(monkeypatch) -> None:
    monkeypatch.setattr(route, "get_position_service", lambda: FakeService())
    response = client.get("/api/v1/positions/portfolio/paper/summary")
    assert response.status_code == 200
    assert response.json()["total_pnl"] == "100"


def test_mark_requires_positive_price(monkeypatch) -> None:
    monkeypatch.setattr(route, "get_position_service", lambda: FakeService())
    response = client.post("/api/v1/positions/position-1/mark", json={"mark_price": 0})
    assert response.status_code == 422
