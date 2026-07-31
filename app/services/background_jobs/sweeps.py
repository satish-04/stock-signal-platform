from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass

from app.services.background_jobs.models import BackgroundJobResult

CandidateLoader = Callable[[], Awaitable[Sequence[str]]]
CandidateProcessor = Callable[[str], Awaitable[str | None]]


@dataclass(frozen=True)
class SweepDefinition:
    load_candidates: CandidateLoader
    process_candidate: CandidateProcessor
    empty_message: str
    completed_message: str


class BackgroundSweepService:
    def __init__(self, **definitions: SweepDefinition) -> None:
        self.definitions = definitions

    @staticmethod
    async def _run_definition(definition: SweepDefinition) -> BackgroundJobResult:
        candidates = list(await definition.load_candidates())
        if not candidates:
            return BackgroundJobResult(0, 0, 0, 0, (definition.empty_message,))
        succeeded = failed = skipped = 0
        details: list[str] = []
        for candidate_id in candidates:
            try:
                message = await definition.process_candidate(candidate_id)
            except Exception as exc:  # noqa: BLE001 - isolate each sweep candidate
                failed += 1
                details.append(f"{candidate_id}: {type(exc).__name__}: {exc}")
            else:
                if message is None:
                    skipped += 1
                    details.append(f"{candidate_id}: skipped")
                else:
                    succeeded += 1
                    details.append(f"{candidate_id}: {message}")
        details.append(definition.completed_message)
        return BackgroundJobResult(len(candidates), succeeded, failed, skipped, tuple(details))

    async def reconcile_workflows(self) -> BackgroundJobResult:
        return await self._run_definition(self.definitions["workflow_reconciliation"])

    async def reconcile_executions(self) -> BackgroundJobResult:
        return await self._run_definition(self.definitions["execution_reconciliation"])

    async def reconcile_positions(self) -> BackgroundJobResult:
        return await self._run_definition(self.definitions["position_reconciliation"])

    async def monitor_exits(self) -> BackgroundJobResult:
        return await self._run_definition(self.definitions["exit_monitoring"])

    async def clean_stale_workflows(self) -> BackgroundJobResult:
        return await self._run_definition(self.definitions["stale_workflow_cleanup"])
