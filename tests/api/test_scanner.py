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


def test_api_starts_without_loading_the_market_data_library() -> None:
    # The scanner's data library is loaded only when a scan runs, so it cannot stop the
    # rest of the API from starting.
    import subprocess
    import sys

    probe = "import sys, app.main; print('yfinance' in sys.modules)"
    result = subprocess.run([sys.executable, "-c", probe], capture_output=True, text=True, check=True)

    assert result.stdout.strip() == "False"
