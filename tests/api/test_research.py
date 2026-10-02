from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ARTIFACT = {
    "symbol": "aapl",
    "provider": "grok-x-research",
    "headline": "Reviewed X research",
    "body": "Research notes",
    "source_id": "grok-run-1",
    "reviewed_by": "analyst",
}


def test_research_routes_are_registered() -> None:
    operations = app.openapi()["paths"]["/api/v1/research/artifacts"]

    assert set(operations) == {"get", "post"}


def test_import_requires_the_webhook_secret() -> None:
    response = client.post(
        "/api/v1/research/artifacts",
        json=ARTIFACT,
        headers={"X-Webhook-Secret": "not-the-secret"},
    )

    assert response.status_code == 401


def test_import_rejects_an_unknown_provider() -> None:
    response = client.post(
        "/api/v1/research/artifacts",
        json={**ARTIFACT, "provider": "somewhere-else"},
        headers={"X-Webhook-Secret": "test-webhook-secret-123456"},
    )

    assert response.status_code == 422
