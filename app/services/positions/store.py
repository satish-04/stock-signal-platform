from __future__ import annotations

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol, cast

from redis.asyncio import Redis

from app.services.positions.models import ExecutionFill, Position


class DuplicateExecutionFillError(RuntimeError):
    """Raised when a fill has already been processed."""


class PositionNotFoundError(LookupError):
    """Raised when a position does not exist."""


class PositionStore(Protocol):
    async def reserve_fill(self, fill_id: str) -> None: ...
    async def save_update(self, position: Position, fill: ExecutionFill) -> None: ...
    async def save_position(self, position: Position) -> None: ...
    async def get_position(self, position_id: str) -> Position | None: ...
    async def get_by_contract(
        self, account_id: str, option_symbol: str, side: str
    ) -> Position | None: ...
    async def get_fill(self, fill_id: str) -> ExecutionFill | None: ...
    async def list_positions(self, account_id: str) -> list[Position]: ...
    async def release_fill(self, fill_id: str) -> None: ...


class InMemoryPositionStore:
    def __init__(self) -> None:
        self._positions: dict[str, Position] = {}
        self._fills: dict[str, ExecutionFill] = {}
        self._reserved: set[str] = set()
        self._by_contract: dict[tuple[str, str, str], str] = {}
        self._lock = asyncio.Lock()

    async def reserve_fill(self, fill_id: str) -> None:
        async with self._lock:
            if fill_id in self._reserved or fill_id in self._fills:
                raise DuplicateExecutionFillError(
                    "This execution fill has already been processed."
                )
            self._reserved.add(fill_id)

    async def save_update(self, position: Position, fill: ExecutionFill) -> None:
        async with self._lock:
            self._save(position)
            self._fills[fill.fill_id] = fill
            self._reserved.discard(fill.fill_id)

    def _save(self, position: Position) -> None:
        self._positions[position.position_id] = position
        self._by_contract[
            (position.account_id, position.option_symbol, position.side)
        ] = position.position_id

    async def save_position(self, position: Position) -> None:
        async with self._lock:
            self._save(position)

    async def get_position(self, position_id: str) -> Position | None:
        async with self._lock:
            return self._positions.get(position_id)

    async def get_by_contract(
        self, account_id: str, option_symbol: str, side: str
    ) -> Position | None:
        async with self._lock:
            position_id = self._by_contract.get((account_id, option_symbol, side))
            return None if position_id is None else self._positions.get(position_id)

    async def get_fill(self, fill_id: str) -> ExecutionFill | None:
        async with self._lock:
            return self._fills.get(fill_id)

    async def list_positions(self, account_id: str) -> list[Position]:
        async with self._lock:
            return [p for p in self._positions.values() if p.account_id == account_id]

    async def release_fill(self, fill_id: str) -> None:
        async with self._lock:
            self._reserved.discard(fill_id)


class RedisPositionStore:
    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        position_ttl_seconds: int,
        fill_lock_ttl_seconds: int,
    ) -> None:
        if not key_prefix.strip() or position_ttl_seconds <= 0 or fill_lock_ttl_seconds <= 0:
            raise ValueError("Position store prefix and TTLs must be valid.")
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.position_ttl_seconds = position_ttl_seconds
        self.fill_lock_ttl_seconds = fill_lock_ttl_seconds

    def _position_key(self, value: str) -> str:
        return f"{self.key_prefix}:position:{value}"

    def _contract_key(self, account: str, contract: str, side: str) -> str:
        return f"{self.key_prefix}:contract:{account}:{side}:{contract}"

    def _fill_key(self, value: str) -> str:
        return f"{self.key_prefix}:fill:{value}"

    def _fill_lock_key(self, value: str) -> str:
        return f"{self.key_prefix}:fill-lock:{value}"

    def _account_key(self, value: str) -> str:
        return f"{self.key_prefix}:account:{value}"

    @staticmethod
    def _serialize(value: Position | ExecutionFill) -> str:
        data = dict(value.__dict__)
        for key, item in tuple(data.items()):
            if isinstance(item, Decimal):
                data[key] = str(item)
            elif isinstance(item, datetime):
                data[key] = item.isoformat()
        return json.dumps(data, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _position(payload: str | bytes) -> Position:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        for field in (
            "average_entry_price", "current_mark_price", "cost_basis", "market_value",
            "realized_pnl", "unrealized_pnl",
        ):
            if data[field] is not None:
                data[field] = Decimal(data[field])
        for field in ("opened_at", "updated_at", "closed_at"):
            if data[field] is not None:
                data[field] = datetime.fromisoformat(data[field])
        return Position(**data)

    @staticmethod
    def _fill(payload: str | bytes) -> ExecutionFill:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        data["fill_price"] = Decimal(data["fill_price"])
        data["filled_at"] = datetime.fromisoformat(data["filled_at"])
        return ExecutionFill(**data)

    async def reserve_fill(self, fill_id: str) -> None:
        if not await self.redis.set(
            self._fill_lock_key(fill_id), "reserved", nx=True, ex=self.fill_lock_ttl_seconds
        ):
            raise DuplicateExecutionFillError(
                "This execution fill has already been processed."
            )
        if await self.redis.get(self._fill_key(fill_id)) is not None:
            await self.redis.delete(self._fill_lock_key(fill_id))
            raise DuplicateExecutionFillError(
                "This execution fill has already been processed."
            )

    async def save_position(self, position: Position) -> None:
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(
            self._position_key(position.position_id), self._serialize(position),
            ex=self.position_ttl_seconds,
        )
        pipe.set(
            self._contract_key(position.account_id, position.option_symbol, position.side),
            position.position_id, ex=self.position_ttl_seconds,
        )
        pipe.sadd(self._account_key(position.account_id), position.position_id)
        pipe.expire(self._account_key(position.account_id), self.position_ttl_seconds)
        await pipe.execute()

    async def save_update(self, position: Position, fill: ExecutionFill) -> None:
        await self.save_position(position)
        pipe = self.redis.pipeline(transaction=True)
        pipe.set(self._fill_key(fill.fill_id), self._serialize(fill), ex=self.position_ttl_seconds)
        pipe.delete(self._fill_lock_key(fill.fill_id))
        await pipe.execute()

    async def get_position(self, position_id: str) -> Position | None:
        payload = await self.redis.get(self._position_key(position_id))
        return None if payload is None else self._position(payload)

    async def get_by_contract(
        self, account_id: str, option_symbol: str, side: str
    ) -> Position | None:
        position_id = await self.redis.get(
            self._contract_key(account_id, option_symbol, side)
        )
        if position_id is None:
            return None
        if isinstance(position_id, bytes):
            position_id = position_id.decode()
        return await self.get_position(cast(str, position_id))

    async def get_fill(self, fill_id: str) -> ExecutionFill | None:
        payload = await self.redis.get(self._fill_key(fill_id))
        return None if payload is None else self._fill(payload)

    async def list_positions(self, account_id: str) -> list[Position]:
        ids = await self.redis.smembers(self._account_key(account_id))
        positions = []
        for position_id in ids:
            if isinstance(position_id, bytes):
                position_id = position_id.decode()
            position = await self.get_position(cast(str, position_id))
            if position is not None:
                positions.append(position)
        return positions

    async def release_fill(self, fill_id: str) -> None:
        await self.redis.delete(self._fill_lock_key(fill_id))
