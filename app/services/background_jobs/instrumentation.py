import time

from app.services.background_jobs.metrics import (
    BACKGROUND_JOB_ACTIVE,
    BACKGROUND_JOB_DURATION,
    BACKGROUND_JOB_ITEMS,
    BACKGROUND_JOB_LAST_SUCCESS,
    BACKGROUND_JOB_RUNS,
    BACKGROUND_SWEEP_CANDIDATES,
)
from app.services.background_jobs.models import BackgroundJobResult, BackgroundJobType
from app.services.background_jobs.service import BackgroundJobHandler


async def instrument_background_handler(
    *, job_type: BackgroundJobType, handler: BackgroundJobHandler
) -> BackgroundJobResult:
    started = time.monotonic()
    BACKGROUND_JOB_ACTIVE.labels(job_type=job_type).inc()
    try:
        result = await handler()
    except Exception:
        BACKGROUND_JOB_RUNS.labels(job_type=job_type, status="FAILED").inc()
        raise
    else:
        BACKGROUND_JOB_RUNS.labels(job_type=job_type, status="SUCCEEDED").inc()
        for outcome, count in (
            ("succeeded", result.succeeded),
            ("failed", result.failed),
            ("skipped", result.skipped),
        ):
            BACKGROUND_JOB_ITEMS.labels(job_type=job_type, outcome=outcome).inc(count)
        BACKGROUND_SWEEP_CANDIDATES.labels(job_type=job_type).set(result.processed)
        BACKGROUND_JOB_LAST_SUCCESS.labels(job_type=job_type).set_to_current_time()
        return result
    finally:
        BACKGROUND_JOB_ACTIVE.labels(job_type=job_type).dec()
        BACKGROUND_JOB_DURATION.labels(job_type=job_type).observe(time.monotonic() - started)
