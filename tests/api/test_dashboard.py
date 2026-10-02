from app.main import app


def test_dashboard_summary_route_is_registered() -> None:
    assert "get" in app.openapi()["paths"]["/api/v1/dashboard/summary"]
