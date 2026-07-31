from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal

BackgroundJobType = Literal[
    "WORKFLOW_RECONCILIATION",
    "EXECUTION_RECONCILIATION",
    "POSITION_RECONCILIATION",
    "EXIT_MONITORING",
    "STALE_WORKFLOW_CLEANUP",
]

BackgroundJobStatus = Literal[
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    "SKIPPED",
    "DEAD_LETTER",
]


@dataclass(frozen=True)
class BackgroundJob:
    job_id: str
    idempotency_key: str
    job_type: BackgroundJobType
    status: BackgroundJobStatus
    scope_id: str | None
    account_id: str | None
    attempt_count: int
    max_attempts: int
    queued_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    result: dict | None
    error_type: str | None
    error_message: str | None
    retryable: bool


@dataclass(frozen=True)
class BackgroundJobResult:
    processed: int
    succeeded: int
    failed: int
    skipped: int
    details: tuple[str, ...]
