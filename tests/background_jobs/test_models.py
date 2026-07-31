from datetime import UTC, datetime

from app.services.background_jobs import BackgroundJob, BackgroundJobResult


def test_background_job_model() -> None:
    timestamp = datetime.now(UTC)
    job = BackgroundJob(
        job_id="job-1",
        idempotency_key="key-1",
        job_type="WORKFLOW_RECONCILIATION",
        status="QUEUED",
        scope_id=None,
        account_id="paper-account",
        attempt_count=0,
        max_attempts=3,
        queued_at=timestamp,
        started_at=None,
        completed_at=None,
        created_at=timestamp,
        updated_at=timestamp,
        result=None,
        error_type=None,
        error_message=None,
        retryable=True,
    )
    assert job.status == "QUEUED"
    assert job.job_type == "WORKFLOW_RECONCILIATION"


def test_background_job_result_model() -> None:
    result = BackgroundJobResult(
        processed=3,
        succeeded=2,
        failed=1,
        skipped=0,
        details=("Processed workflows.",),
    )
    assert result.processed == 3
    assert result.succeeded == 2
