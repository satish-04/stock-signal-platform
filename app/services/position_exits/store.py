import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol

from redis.asyncio import Redis

from app.services.position_exits.models import PositionExitSignal


class DuplicatePositionExitError(RuntimeError):
    """Raised when an equivalent exit signal already exists."""


class PositionExitSignalNotFoundError(LookupError):
    """Raised when an exit signal does not exist."""


class PositionExitStore(Protocol):
    async def reserve(self, key: str, signal_id: str) -> None: ...
    async def save(self, signal: PositionExitSignal) -> None: ...
    async def get(self, signal_id: str) -> PositionExitSignal | None: ...
    async def list_for_position(self, position_id: str) -> list[PositionExitSignal]: ...


class InMemoryPositionExitStore:
    def __init__(self) -> None:
        self._signals: dict[str, PositionExitSignal] = {}
        self._keys: dict[str, str] = {}
        self._lock = asyncio.Lock()

    async def reserve(self, key: str, signal_id: str) -> None:
        async with self._lock:
            if key in self._keys:
                raise DuplicatePositionExitError("An equivalent exit signal already exists.")
            self._keys[key] = signal_id

    async def save(self, signal: PositionExitSignal) -> None:
        async with self._lock:
            self._signals[signal.exit_signal_id] = signal

    async def get(self, signal_id: str) -> PositionExitSignal | None:
        async with self._lock:
            return self._signals.get(signal_id)

    async def list_for_position(self, position_id: str) -> list[PositionExitSignal]:
        async with self._lock:
            return [s for s in self._signals.values() if s.position_id == position_id]


class RedisPositionExitStore:
    def __init__(self, redis: Redis, *, prefix: str, ttl: int, lock_ttl: int) -> None:
        if not prefix.strip() or ttl <= 0 or lock_ttl <= 0:
            raise ValueError("Exit store prefix and TTLs must be valid.")
        self.redis, self.prefix, self.ttl, self.lock_ttl = redis, prefix.rstrip(":"), ttl, lock_ttl

    def _signal(self, value: str) -> str:
        return f"{self.prefix}:signal:{value}"

    def _lock(self, value: str) -> str:
        return f"{self.prefix}:lock:{value}"

    def _position(self, value: str) -> str:
        return f"{self.prefix}:position:{value}"

    @staticmethod
    def _serialize(signal: PositionExitSignal) -> str:
        data = dict(signal.__dict__)
        for key, value in tuple(data.items()):
            if isinstance(value, Decimal):
                data[key] = str(value)
            elif isinstance(value, datetime):
                data[key] = value.isoformat()
            elif isinstance(value, tuple):
                data[key] = list(value)
        return json.dumps(data, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _deserialize(payload: str | bytes) -> PositionExitSignal:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        data["mark_price"] = Decimal(data["mark_price"])
        if data["trigger_price"] is not None:
            data["trigger_price"] = Decimal(data["trigger_price"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        data["explanations"] = tuple(data["explanations"])
        data["rejection_reasons"] = tuple(data["rejection_reasons"])
        return PositionExitSignal(**data)

    async def reserve(self, key: str, signal_id: str) -> None:
        if not await self.redis.set(self._lock(key), signal_id, nx=True, ex=self.lock_ttl):
            raise DuplicatePositionExitError("An equivalent exit signal already exists.")

    async def save(self, signal: PositionExitSignal) -> None:
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(self._signal(signal.exit_signal_id), self._serialize(signal), ex=self.ttl)
        pipe.sadd(self._position(signal.position_id), signal.exit_signal_id)
        pipe.expire(self._position(signal.position_id), self.ttl)
        await pipe.execute()

    async def get(self, signal_id: str) -> PositionExitSignal | None:
        payload = await self.redis.get(self._signal(signal_id))
        return None if payload is None else self._deserialize(payload)

    async def list_for_position(self, position_id: str) -> list[PositionExitSignal]:
        signals = []
        for signal_id in await self.redis.smembers(self._position(position_id)):
            if isinstance(signal_id, bytes):
                signal_id = signal_id.decode()
            signal = await self.get(signal_id)
            if signal:
                signals.append(signal)
        return signals
