from __future__ import annotations

import asyncio
import json
from dataclasses import fields
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from redis.asyncio import Redis

from app.services.broker_events.models import (
    BrokerCommissionPayload,
    BrokerErrorPayload,
    BrokerEvent,
    BrokerEventPayload,
    BrokerExecutionPayload,
    BrokerOrderStatusPayload,
)


class DuplicateBrokerEventError(RuntimeError):
    """Raised when a broker event with the same idempotency key was already received."""


class BrokerEventStore(Protocol):
    async def reserve(self, idempotency_key: str, event_id: str) -> None: ...
    async def save(self, event: BrokerEvent) -> None: ...
    async def get(self, event_id: str) -> BrokerEvent | None: ...
    async def get_by_idempotency_key(self, idempotency_key: str) -> BrokerEvent | None: ...
    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]: ...
    async def list_ids_for_broker_order(self, broker_order_id: str, *, limit: int) -> list[str]: ...
    async def list_ids_for_execution(self, execution_id: str, *, limit: int) -> list[str]: ...
    async def release(self, idempotency_key: str) -> None: ...


class InMemoryBrokerEventStore:
    def __init__(self) -> None:
        self._events: dict[str, BrokerEvent] = {}
        self._keys: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def reserve(self, idempotency_key: str, event_id: str) -> None:
        async with self._lock:
            if idempotency_key in self._keys:
                raise DuplicateBrokerEventError("This broker event was already received.")
            self._keys[idempotency_key] = event_id

    async def save(self, event: BrokerEvent) -> None:
        async with self._lock:
            self._events[event.event_id] = event
            self._keys[event.idempotency_key] = event.event_id

    async def get(self, event_id: str) -> BrokerEvent | None:
        async with self._lock:
            return self._events.get(event_id)

    async def get_by_idempotency_key(self, idempotency_key: str) -> BrokerEvent | None:
        async with self._lock:
            event_id = self._keys.get(idempotency_key)
            return None if event_id is None else self._events.get(event_id)

    def _ids(self, predicate, limit: int) -> list[str]:
        events = sorted(
            (e for e in self._events.values() if predicate(e)), key=lambda e: e.received_at
        )
        return [e.event_id for e in events[:limit]]

    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]:
        async with self._lock:
            return self._ids(lambda e: e.status in statuses, limit)

    async def list_ids_for_broker_order(self, broker_order_id: str, *, limit: int) -> list[str]:
        async with self._lock:
            return self._ids(lambda e: e.broker_order_id == broker_order_id, limit)

    async def list_ids_for_execution(self, execution_id: str, *, limit: int) -> list[str]:
        async with self._lock:
            return self._ids(lambda e: e.execution_id == execution_id, limit)

    async def release(self, idempotency_key: str) -> None:
        async with self._lock:
            event_id = self._keys.get(idempotency_key)
            if event_id is not None and event_id not in self._events:
                del self._keys[idempotency_key]


_PAYLOAD_TYPES: dict[str, type] = {
    "ORDER_STATUS": BrokerOrderStatusPayload,
    "EXECUTION_DETAILS": BrokerExecutionPayload,
    "COMMISSION_REPORT": BrokerCommissionPayload,
    "BROKER_ERROR": BrokerErrorPayload,
}
_EVENT_DATETIMES = ("received_at", "processing_started_at", "processed_at", "created_at", "updated_at")


def _encode(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _decode_payload(event_type: str, data: dict[str, Any]) -> BrokerEventPayload:
    payload_type = _PAYLOAD_TYPES[event_type]
    for field in fields(payload_type):
        value = data.get(field.name)
        if value is None:
            continue
        if "Decimal" in str(field.type):
            data[field.name] = Decimal(value)
        elif "datetime" in str(field.type):
            data[field.name] = datetime.fromisoformat(value)
    return payload_type(**data)


def serialize_event(event: BrokerEvent) -> str:
    data = {key: _encode(value) for key, value in event.__dict__.items() if key != "payload"}
    data["payload"] = {key: _encode(value) for key, value in event.payload.__dict__.items()}
    return json.dumps(data, separators=(",", ":"), sort_keys=True)


def deserialize_event(payload: str | bytes) -> BrokerEvent:
    if isinstance(payload, bytes):
        payload = payload.decode()
    data: dict[str, Any] = json.loads(payload)
    data["payload"] = _decode_payload(data["event_type"], data["payload"])
    for key in _EVENT_DATETIMES:
        if data[key] is not None:
            data[key] = datetime.fromisoformat(data[key])
    return BrokerEvent(**data)


class RedisBrokerEventStore:
    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        event_ttl_seconds: int,
        lock_ttl_seconds: int,
    ) -> None:
        if not key_prefix.strip() or event_ttl_seconds <= 0 or lock_ttl_seconds <= 0:
            raise ValueError("Broker event store prefix and TTLs must be valid.")
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.event_ttl_seconds = event_ttl_seconds
        self.lock_ttl_seconds = lock_ttl_seconds

    def _event_key(self, value: str) -> str:
        return f"{self.key_prefix}:event:{value}"

    def _idempotency_key(self, value: str) -> str:
        return f"{self.key_prefix}:idempotency:{value}"

    def _status_key(self, value: str) -> str:
        return f"{self.key_prefix}:status:{value}"

    def _broker_order_key(self, value: str) -> str:
        return f"{self.key_prefix}:broker-order:{value}"

    def _execution_key(self, value: str) -> str:
        return f"{self.key_prefix}:execution:{value}"

    async def reserve(self, idempotency_key: str, event_id: str) -> None:
        if not await self.redis.set(
            self._idempotency_key(idempotency_key), event_id, nx=True, ex=self.lock_ttl_seconds
        ):
            raise DuplicateBrokerEventError("This broker event was already received.")

    async def save(self, event: BrokerEvent) -> None:
        score = event.received_at.timestamp()
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(self._event_key(event.event_id), serialize_event(event), ex=self.event_ttl_seconds)
        pipe.set(
            self._idempotency_key(event.idempotency_key), event.event_id,
            ex=self.event_ttl_seconds,
        )
        for status in _ALL_STATUSES:
            pipe.zrem(self._status_key(status), event.event_id)
        pipe.zadd(self._status_key(event.status), {event.event_id: score})
        if event.broker_order_id:
            pipe.zadd(self._broker_order_key(event.broker_order_id), {event.event_id: score})
            pipe.expire(self._broker_order_key(event.broker_order_id), self.event_ttl_seconds)
        if event.execution_id:
            pipe.zadd(self._execution_key(event.execution_id), {event.event_id: score})
            pipe.expire(self._execution_key(event.execution_id), self.event_ttl_seconds)
        await pipe.execute()

    async def get(self, event_id: str) -> BrokerEvent | None:
        payload = await self.redis.get(self._event_key(event_id))
        return None if payload is None else deserialize_event(payload)

    async def get_by_idempotency_key(self, idempotency_key: str) -> BrokerEvent | None:
        event_id = await self.redis.get(self._idempotency_key(idempotency_key))
        if event_id is None:
            return None
        return await self.get(event_id.decode() if isinstance(event_id, bytes) else event_id)

    async def _range(self, key: str, limit: int) -> list[str]:
        values = await self.redis.zrange(key, 0, limit - 1)
        return [v.decode() if isinstance(v, bytes) else v for v in values]

    async def list_ids_by_statuses(self, statuses: tuple[str, ...], *, limit: int) -> list[str]:
        candidates: dict[str, float] = {}
        for status in statuses:
            rows = await self.redis.zrange(self._status_key(status), 0, limit - 1, withscores=True)
            for value, score in rows:
                key = value.decode() if isinstance(value, bytes) else value
                candidates[key] = float(score)
        return [key for key, _ in sorted(candidates.items(), key=lambda item: item[1])[:limit]]

    async def list_ids_for_broker_order(self, broker_order_id: str, *, limit: int) -> list[str]:
        return await self._range(self._broker_order_key(broker_order_id), limit)

    async def list_ids_for_execution(self, execution_id: str, *, limit: int) -> list[str]:
        return await self._range(self._execution_key(execution_id), limit)

    async def release(self, idempotency_key: str) -> None:
        key = self._idempotency_key(idempotency_key)
        event_id = await self.redis.get(key)
        if event_id is None:
            return
        event_id = event_id.decode() if isinstance(event_id, bytes) else event_id
        if await self.redis.get(self._event_key(event_id)) is None:
            await self.redis.delete(key)


_ALL_STATUSES = ("RECEIVED", "PROCESSING", "PROCESSED", "SKIPPED", "FAILED", "DEAD_LETTER")
