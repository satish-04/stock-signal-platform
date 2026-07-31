from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.services.background_jobs.models import BackgroundJob

client = TestClient(app)


def build_job() -> BackgroundJob:
    now = datetime.now(UTC)
    return BackgroundJob("job-test", "key-test", "EXIT_MONITORING", "SUCCEEDED", None,
        "paper-account", 1, 3, now, now, now, now, now,
        {"processed": 1, "succeeded": 1}, None, None, False)


class StubJobService:
    def __init__(self, **kwargs): pass
    async def get(self, job_id: str):
        assert job_id == "job-test"
        return build_job()


def test_get_background_job(monkeypatch) -> None:
    monkeypatch.setattr("app.api.routes.background_jobs.BackgroundJobService", StubJobService)
    monkeypatch.setattr("app.api.routes.background_jobs.get_background_job_store", lambda: object())
    response = client.get("/api/v1/background-jobs/job-test")
    assert response.status_code == 200
    assert response.json()["status"] == "SUCCEEDED"
