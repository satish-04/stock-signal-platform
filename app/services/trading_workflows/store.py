import asyncio
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Protocol

from redis.asyncio import Redis

from app.services.trading_workflows.models import (
    TradingWorkflow,
    WorkflowEvent,
    WorkflowFailure,
    WorkflowReference,
)


class DuplicateTradingWorkflowError(RuntimeError):
    """Raised when an idempotent workflow already exists."""


class TradingWorkflowNotFoundError(LookupError):
    """Raised when a workflow does not exist."""


class TradingWorkflowStore(Protocol):
    async def reserve(self, key: str, workflow_id: str) -> None: ...
    async def save(self, workflow: TradingWorkflow) -> None: ...
    async def get(self, workflow_id: str) -> TradingWorkflow | None: ...
    async def list_for_account(self, account_id: str) -> list[TradingWorkflow]: ...
    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]: ...
    async def list_ids_updated_before(self, statuses: tuple[str, ...], *, updated_before: datetime, limit: int) -> list[str]: ...
    async def get_by_execution_id(self, execution_id: str) -> TradingWorkflow | None: ...
    async def get_by_position_id(self, position_id: str) -> TradingWorkflow | None: ...
    async def list_account_ids(self, *, limit: int) -> list[str]: ...


class InMemoryTradingWorkflowStore:
    def __init__(self) -> None:
        self.workflows: dict[str, TradingWorkflow] = {}
        self.keys: dict[str, str] = {}
        self.lock = asyncio.Lock()
        self._by_execution: dict[str, str] = {}
        self._by_position: dict[str, str] = {}
        self._accounts: set[str] = set()

    async def reserve(self, key: str, workflow_id: str) -> None:
        async with self.lock:
            if key in self.keys:
                raise DuplicateTradingWorkflowError("Workflow already exists.")
            self.keys[key] = workflow_id

    async def save(self, workflow: TradingWorkflow) -> None:
        async with self.lock:
            self.workflows[workflow.workflow_id] = workflow
            self._accounts.add(workflow.account_id)
            if workflow.reference.execution_id:
                self._by_execution[workflow.reference.execution_id] = workflow.workflow_id
            if workflow.reference.position_id:
                self._by_position[workflow.reference.position_id] = workflow.workflow_id

    async def get(self, workflow_id: str) -> TradingWorkflow | None:
        async with self.lock:
            return self.workflows.get(workflow_id)

    async def list_for_account(self, account_id: str) -> list[TradingWorkflow]:
        async with self.lock:
            return [w for w in self.workflows.values() if w.account_id == account_id]

    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]:
        async with self.lock:
            values = sorted(
                (w for w in self.workflows.values() if w.status in statuses),
                key=lambda w: w.updated_at,
            )
            return [w.workflow_id for w in values[:limit]]

    async def list_ids_updated_before(self, statuses: tuple[str, ...], *, updated_before: datetime, limit: int) -> list[str]:
        async with self.lock:
            values = sorted(
                (w for w in self.workflows.values() if w.status in statuses and w.updated_at < updated_before),
                key=lambda w: w.updated_at,
            )
            return [w.workflow_id for w in values[:limit]]

    async def get_by_execution_id(self, execution_id: str) -> TradingWorkflow | None:
        async with self.lock:
            value = self._by_execution.get(execution_id)
            return self.workflows.get(value) if value else None

    async def get_by_position_id(self, position_id: str) -> TradingWorkflow | None:
        async with self.lock:
            value = self._by_position.get(position_id)
            return self.workflows.get(value) if value else None

    async def list_account_ids(self, *, limit: int) -> list[str]:
        async with self.lock:
            return sorted(self._accounts)[:limit]


class RedisTradingWorkflowStore:
    def __init__(self, redis: Redis, *, prefix: str, ttl: int, lock_ttl: int) -> None:
        if not prefix.strip() or ttl <= 0 or lock_ttl <= 0:
            raise ValueError("Workflow prefix and TTLs must be valid.")
        self.redis, self.prefix, self.ttl, self.lock_ttl = redis, prefix.rstrip(":"), ttl, lock_ttl

    def _workflow(self, value: str) -> str:
        return f"{self.prefix}:workflow:{value}"

    def _lock(self, value: str) -> str:
        return f"{self.prefix}:lock:{value}"

    def _account(self, value: str) -> str:
        return f"{self.prefix}:account:{value}"

    def _status(self, value: str) -> str:
        return f"{self.prefix}:status:{value}"

    def _accounts(self) -> str:
        return f"{self.prefix}:accounts"

    def _execution(self, value: str) -> str:
        return f"{self.prefix}:execution:{value}"

    def _position(self, value: str) -> str:
        return f"{self.prefix}:position:{value}"

    @staticmethod
    def _serialize(workflow: TradingWorkflow) -> str:
        return json.dumps(
            asdict(workflow),
            default=lambda value: value.isoformat() if isinstance(value, datetime) else value,
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def _deserialize(payload: str | bytes) -> TradingWorkflow:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        reference = WorkflowReference(**data.pop("reference"))
        failure_data = data.pop("failure")
        failure = None
        if failure_data:
            failure_data["occurred_at"] = datetime.fromisoformat(failure_data["occurred_at"])
            failure = WorkflowFailure(**failure_data)
        events = []
        for event in data.pop("events"):
            event["created_at"] = datetime.fromisoformat(event["created_at"])
            events.append(WorkflowEvent(**event))
        for field in ("approved_at", "created_at", "updated_at", "completed_at"):
            if data[field] is not None:
                data[field] = datetime.fromisoformat(data[field])
        return TradingWorkflow(reference=reference, failure=failure, events=tuple(events), **data)

    async def reserve(self, key: str, workflow_id: str) -> None:
        if not await self.redis.set(self._lock(key), workflow_id, nx=True, ex=self.lock_ttl):
            raise DuplicateTradingWorkflowError("Workflow already exists.")

    async def save(self, workflow: TradingWorkflow) -> None:
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(self._workflow(workflow.workflow_id), self._serialize(workflow), ex=self.ttl)
        pipe.sadd(self._account(workflow.account_id), workflow.workflow_id)
        pipe.expire(self._account(workflow.account_id), self.ttl)
        for status in (
            "CREATED", "RECOMMENDATION_READY", "RISK_APPROVED", "RISK_REJECTED",
            "AWAITING_APPROVAL", "APPROVED", "INTENT_CREATED", "EXECUTION_CREATED",
            "SUBMISSION_PENDING", "SUBMITTED", "PARTIALLY_FILLED", "FILLED",
            "POSITION_RECONCILED", "EXIT_MONITORING", "EXIT_SIGNAL_CREATED",
            "EXIT_INTENT_CREATED", "EXIT_EXECUTION_CREATED", "COMPLETED", "FAILED", "CANCELLED",
        ):
            pipe.zrem(self._status(status), workflow.workflow_id)
        pipe.zadd(self._status(workflow.status), {workflow.workflow_id: workflow.updated_at.timestamp()})
        pipe.sadd(self._accounts(), workflow.account_id)
        if workflow.reference.execution_id:
            pipe.set(self._execution(workflow.reference.execution_id), workflow.workflow_id, ex=self.ttl)
        if workflow.reference.position_id:
            pipe.set(self._position(workflow.reference.position_id), workflow.workflow_id, ex=self.ttl)
        await pipe.execute()

    async def get(self, workflow_id: str) -> TradingWorkflow | None:
        payload = await self.redis.get(self._workflow(workflow_id))
        return None if payload is None else self._deserialize(payload)

    async def list_for_account(self, account_id: str) -> list[TradingWorkflow]:
        values = []
        for workflow_id in await self.redis.smembers(self._account(account_id)):
            if isinstance(workflow_id, bytes):
                workflow_id = workflow_id.decode()
            workflow = await self.get(workflow_id)
            if workflow:
                values.append(workflow)
        return values

    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]:
        candidates: dict[str, float] = {}
        for status in statuses:
            for value, score in await self.redis.zrange(self._status(status), 0, limit - 1, withscores=True):
                key = value.decode() if isinstance(value, bytes) else value
                candidates[key] = min(candidates.get(key, float(score)), float(score))
        return [key for key, _ in sorted(candidates.items(), key=lambda item: item[1])[:limit]]

    async def list_ids_updated_before(self, statuses: tuple[str, ...], *, updated_before: datetime, limit: int) -> list[str]:
        candidates: dict[str, float] = {}
        for status in statuses:
            rows = await self.redis.zrangebyscore(
                self._status(status), "-inf", updated_before.timestamp(), start=0, num=limit, withscores=True
            )
            for value, score in rows:
                key = value.decode() if isinstance(value, bytes) else value
                candidates[key] = float(score)
        return [key for key, _ in sorted(candidates.items(), key=lambda item: item[1])[:limit]]

    async def _get_reference(self, key: str) -> TradingWorkflow | None:
        value = await self.redis.get(key)
        if value is None:
            return None
        return await self.get(value.decode() if isinstance(value, bytes) else value)

    async def get_by_execution_id(self, execution_id: str) -> TradingWorkflow | None:
        return await self._get_reference(self._execution(execution_id))

    async def get_by_position_id(self, position_id: str) -> TradingWorkflow | None:
        return await self._get_reference(self._position(position_id))

    async def list_account_ids(self, *, limit: int) -> list[str]:
        values = await self.redis.smembers(self._accounts())
        return sorted(v.decode() if isinstance(v, bytes) else v for v in values)[:limit]
