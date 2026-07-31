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


class InMemoryTradingWorkflowStore:
    def __init__(self) -> None:
        self.workflows: dict[str, TradingWorkflow] = {}
        self.keys: dict[str, str] = {}
        self.lock = asyncio.Lock()

    async def reserve(self, key: str, workflow_id: str) -> None:
        async with self.lock:
            if key in self.keys:
                raise DuplicateTradingWorkflowError("Workflow already exists.")
            self.keys[key] = workflow_id

    async def save(self, workflow: TradingWorkflow) -> None:
        async with self.lock:
            self.workflows[workflow.workflow_id] = workflow

    async def get(self, workflow_id: str) -> TradingWorkflow | None:
        async with self.lock:
            return self.workflows.get(workflow_id)

    async def list_for_account(self, account_id: str) -> list[TradingWorkflow]:
        async with self.lock:
            return [w for w in self.workflows.values() if w.account_id == account_id]


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
