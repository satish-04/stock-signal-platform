from datetime import UTC, datetime

from app.services.background_jobs import SweepCandidate


def test_sweep_candidate_is_immutable() -> None:
    candidate = SweepCandidate("workflow-1", "WORKFLOW", "APPROVED", "paper", datetime.now(UTC))
    assert candidate.candidate_id == "workflow-1"
    assert candidate.candidate_type == "WORKFLOW"
