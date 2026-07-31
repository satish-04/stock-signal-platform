from __future__ import annotations

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, cast

from redis.asyncio import Redis

from app.services.order_execution.models import OrderExecution


class DuplicateOrderExecutionError(RuntimeError):
    """Raised when an execution already exists for an intent."""


class OrderExecutionNotFoundError(LookupError):
    """Raised when an execution record cannot be found."""


class OrderExecutionStore(Protocol):
    async def reserve(self, intent_id: str, execution_id: str) -> None: ...
    async def save(self, execution: OrderExecution) -> None: ...
    async def get(self, execution_id: str) -> OrderExecution | None: ...
    async def get_by_intent_id(self, intent_id: str) -> OrderExecution | None: ...
    async def get_by_broker_order_id(
        self, broker_order_id: str
    ) -> OrderExecution | None: ...
    async def delete(self, execution: OrderExecution) -> None: ...


class InMemoryOrderExecutionStore:
    def __init__(self) -> None:
        self._executions: dict[str, OrderExecution] = {}
        self._by_intent: dict[str, str] = {}
        self._by_broker: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def reserve(self, intent_id: str, execution_id: str) -> None:
        async with self._lock:
            if intent_id in self._by_intent:
                raise DuplicateOrderExecutionError(
                    "An execution already exists for this order intent."
                )
            self._by_intent[intent_id] = execution_id

    async def save(self, execution: OrderExecution) -> None:
        async with self._lock:
            self._executions[execution.execution_id] = execution
            self._by_intent[execution.intent_id] = execution.execution_id
            if execution.broker_order_id:
                self._by_broker[execution.broker_order_id] = execution.execution_id

    async def get(self, execution_id: str) -> OrderExecution | None:
        async with self._lock:
            return self._executions.get(execution_id)

    async def get_by_intent_id(self, intent_id: str) -> OrderExecution | None:
        async with self._lock:
            execution_id = self._by_intent.get(intent_id)
            return None if execution_id is None else self._executions.get(execution_id)

    async def get_by_broker_order_id(
        self, broker_order_id: str
    ) -> OrderExecution | None:
        async with self._lock:
            execution_id = self._by_broker.get(broker_order_id)
            return None if execution_id is None else self._executions.get(execution_id)

    async def delete(self, execution: OrderExecution) -> None:
        async with self._lock:
            self._executions.pop(execution.execution_id, None)
            self._by_intent.pop(execution.intent_id, None)
            if execution.broker_order_id:
                self._by_broker.pop(execution.broker_order_id, None)


class RedisOrderExecutionStore:
    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        execution_ttl_seconds: int,
        lock_ttl_seconds: int,
    ) -> None:
        if not key_prefix.strip():
            raise ValueError("key_prefix must not be empty.")
        if execution_ttl_seconds <= 0 or lock_ttl_seconds <= 0:
            raise ValueError("execution and lock TTLs must be greater than zero.")
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.execution_ttl_seconds = execution_ttl_seconds
        self.lock_ttl_seconds = lock_ttl_seconds

    def _execution_key(self, value: str) -> str:
        return f"{self.key_prefix}:execution:{value}"

    def _intent_key(self, value: str) -> str:
        return f"{self.key_prefix}:intent:{value}"

    def _broker_key(self, value: str) -> str:
        return f"{self.key_prefix}:broker:{value}"

    @staticmethod
    def _serialize(execution: OrderExecution) -> str:
        data = dict(execution.__dict__)
        data["limit_price"] = str(execution.limit_price)
        data["average_fill_price"] = (
            None
            if execution.average_fill_price is None
            else str(execution.average_fill_price)
        )
        for field in (
            "submitted_at",
            "acknowledged_at",
            "completed_at",
            "created_at",
            "updated_at",
        ):
            value = getattr(execution, field)
            data[field] = None if value is None else value.isoformat()
        return json.dumps(data, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _deserialize(payload: str | bytes) -> OrderExecution:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        data["limit_price"] = Decimal(data["limit_price"])
        if data["average_fill_price"] is not None:
            data["average_fill_price"] = Decimal(data["average_fill_price"])
        for field in (
            "submitted_at",
            "acknowledged_at",
            "completed_at",
            "created_at",
            "updated_at",
        ):
            if data[field] is not None:
                data[field] = datetime.fromisoformat(data[field])
        return OrderExecution(**data)

    async def reserve(self, intent_id: str, execution_id: str) -> None:
        reserved = await self.redis.set(
            self._intent_key(intent_id),
            execution_id,
            nx=True,
            ex=self.lock_ttl_seconds,
        )
        if not reserved:
            raise DuplicateOrderExecutionError(
                "An execution already exists for this order intent."
            )

    async def save(self, execution: OrderExecution) -> None:
        pipeline = self.redis.pipeline(transaction=True)
        pipeline.set(
            self._execution_key(execution.execution_id),
            self._serialize(execution),
            ex=self.execution_ttl_seconds,
        )
        pipeline.set(
            self._intent_key(execution.intent_id),
            execution.execution_id,
            ex=self.execution_ttl_seconds,
        )
        if execution.broker_order_id:
            pipeline.set(
                self._broker_key(execution.broker_order_id),
                execution.execution_id,
                ex=self.execution_ttl_seconds,
            )
        await pipeline.execute()

    async def get(self, execution_id: str) -> OrderExecution | None:
        payload = await self.redis.get(self._execution_key(execution_id))
        return None if payload is None else self._deserialize(payload)

    async def _get_indexed(self, key: str) -> OrderExecution | None:
        execution_id = await self.redis.get(key)
        if execution_id is None:
            return None
        if isinstance(execution_id, bytes):
            execution_id = execution_id.decode()
        return await self.get(cast(str, execution_id))

    async def get_by_intent_id(self, intent_id: str) -> OrderExecution | None:
        return await self._get_indexed(self._intent_key(intent_id))

    async def get_by_broker_order_id(
        self, broker_order_id: str
    ) -> OrderExecution | None:
        return await self._get_indexed(self._broker_key(broker_order_id))

    async def delete(self, execution: OrderExecution) -> None:
        keys = [
            self._execution_key(execution.execution_id),
            self._intent_key(execution.intent_id),
        ]
        if execution.broker_order_id:
            keys.append(self._broker_key(execution.broker_order_id))
        await self.redis.delete(*keys)
