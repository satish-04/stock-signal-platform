from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_scanner_routes_are_registered() -> None:
    paths = app.openapi()["paths"]

    assert "/api/v1/scanner/options" in paths
    assert "/api/v1/scanner/options/latest" in paths
    assert "/api/v1/scanner/options/{scan_id}" in paths


def test_scan_rejects_malformed_symbols() -> None:
    response = client.post("/api/v1/scanner/options", json={"symbols": ["NVDA; DROP"]})

    assert response.status_code == 422


def test_scan_rejects_an_expiry_in_the_past() -> None:
    response = client.post("/api/v1/scanner/options", json={"expiry": "2020-01-03"})

    assert response.status_code == 422
    assert response.json()["detail"] == "Expiry must be today or later"
