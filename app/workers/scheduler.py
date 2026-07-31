from __future__ import annotations

import time

from app.core.config import get_settings
from app.workers.tasks import (
    execution_reconciliation,
    exit_monitoring,
    position_reconciliation,
    stale_workflow_cleanup,
    workflow_reconciliation,
)


def run_scheduler() -> None:
    settings = get_settings()
    schedules = (
        (settings.workflow_reconciliation_interval_seconds, workflow_reconciliation),
        (settings.execution_reconciliation_interval_seconds, execution_reconciliation),
        (settings.position_reconciliation_interval_seconds, position_reconciliation),
        (settings.exit_monitoring_interval_seconds, exit_monitoring),
        (settings.stale_workflow_cleanup_interval_seconds, stale_workflow_cleanup),
    )
    last_runs = [0.0] * len(schedules)
    while True:
        if not settings.background_automation_enabled:
            time.sleep(5)
            continue
        now = time.monotonic()
        for index, (interval, actor) in enumerate(schedules):
            if now - last_runs[index] >= interval:
                actor.send()
                last_runs[index] = now
        time.sleep(1)


if __name__ == "__main__":
    run_scheduler()
