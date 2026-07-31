from app.services.background_jobs import BackgroundSweepService, SweepDefinition


async def test_sweep_processes_success_failure_and_skip() -> None:
    async def load(): return ["one", "two", "three"]
    async def process(item):
        if item == "two": raise RuntimeError("failed")
        return None if item == "three" else "completed"
    definition = SweepDefinition(load, process, "empty", "done")
    service = BackgroundSweepService(**{name: definition for name in (
        "workflow_reconciliation", "execution_reconciliation", "position_reconciliation",
        "exit_monitoring", "stale_workflow_cleanup")})
    result = await service.reconcile_workflows()
    assert (result.processed, result.succeeded, result.failed, result.skipped) == (3, 1, 1, 1)


async def test_empty_sweep_returns_zero_counts() -> None:
    async def load(): return []
    async def process(item): raise AssertionError(item)
    definition = SweepDefinition(load, process, "nothing found", "done")
    service = BackgroundSweepService(**{name: definition for name in (
        "workflow_reconciliation", "execution_reconciliation", "position_reconciliation",
        "exit_monitoring", "stale_workflow_cleanup")})
    result = await service.monitor_exits()
    assert result.processed == 0
    assert result.details == ("nothing found",)
