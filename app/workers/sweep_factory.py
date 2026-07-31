from functools import lru_cache

from app.services.background_jobs import BackgroundSweepService, SweepDefinition


async def _empty_candidates() -> list[str]:
    return []


async def _safe_placeholder(candidate_id: str) -> str | None:
    del candidate_id
    return None


@lru_cache(maxsize=1)
def get_background_sweep_service() -> BackgroundSweepService:
    messages = {
        "workflow_reconciliation": ("No workflows require reconciliation.", "Workflow reconciliation sweep completed."),
        "execution_reconciliation": ("No executions require reconciliation.", "Execution reconciliation sweep completed."),
        "position_reconciliation": ("No fills require position reconciliation.", "Position reconciliation sweep completed."),
        "exit_monitoring": ("No open positions require exit monitoring.", "Exit-monitoring sweep completed."),
        "stale_workflow_cleanup": ("No stale workflows were found.", "Stale-workflow cleanup sweep completed."),
    }
    return BackgroundSweepService(**{
        name: SweepDefinition(_empty_candidates, _safe_placeholder, empty, completed)
        for name, (empty, completed) in messages.items()
    })
