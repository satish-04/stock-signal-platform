from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.services.order_intents.models import OrderIntent
from app.services.order_intents.store import DuplicateOrderIntentError


class RedisOrderIntentStore:
    def __init__(
        self,
        redis: Redis,
        *,
        key_prefix: str,
        intent_ttl_seconds: int,
        lock_ttl_seconds: int,
    ) -> None:
        if not key_prefix.strip():
            raise ValueError("key_prefix must not be empty.")
        if intent_ttl_seconds <= 0:
            raise ValueError("intent_ttl_seconds must be greater than zero.")
        if lock_ttl_seconds <= 0:
            raise ValueError("lock_ttl_seconds must be greater than zero.")
        self.redis = redis
        self.key_prefix = key_prefix.rstrip(":")
        self.intent_ttl_seconds = intent_ttl_seconds
        self.lock_ttl_seconds = lock_ttl_seconds

    def _intent_key(self, intent_id: str) -> str:
        return f"{self.key_prefix}:intent:{intent_id}"

    def _idempotency_key(self, idempotency_key: str) -> str:
        return f"{self.key_prefix}:idempotency:{idempotency_key}"

    @staticmethod
    def _serialize(intent: OrderIntent) -> str:
        payload = {
            **intent.__dict__,
            "limit_price": str(intent.limit_price),
            "estimated_debit": str(intent.estimated_debit),
            "maximum_loss": str(intent.maximum_loss),
            "stop_price": str(intent.stop_price),
            "first_target_price": str(intent.first_target_price),
            "second_target_price": str(intent.second_target_price),
            "created_at": intent.created_at.isoformat(),
            "reasons": list(intent.reasons),
            "rejection_reasons": list(intent.rejection_reasons),
        }
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)

    @staticmethod
    def _deserialize(payload: str | bytes) -> OrderIntent:
        if isinstance(payload, bytes):
            payload = payload.decode()
        data: dict[str, Any] = json.loads(payload)
        for field in (
            "limit_price",
            "estimated_debit",
            "maximum_loss",
            "stop_price",
            "first_target_price",
            "second_target_price",
        ):
            data[field] = Decimal(data[field])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        data["reasons"] = tuple(data["reasons"])
        data["rejection_reasons"] = tuple(data["rejection_reasons"])
        return OrderIntent(**data)

    async def reserve(self, idempotency_key: str, intent_id: str) -> None:
        reserved = await self.redis.set(
            self._idempotency_key(idempotency_key),
            intent_id,
            nx=True,
            ex=self.lock_ttl_seconds,
        )
        if not reserved:
            raise DuplicateOrderIntentError(
                "An order intent with this idempotency key has already been registered."
            )

    async def save(self, intent: OrderIntent) -> None:
        transaction = self.redis.pipeline(transaction=True)
        transaction.set(
            self._intent_key(intent.intent_id),
            self._serialize(intent),
            ex=self.intent_ttl_seconds,
        )
        transaction.set(
            self._idempotency_key(intent.idempotency_key),
            intent.intent_id,
            ex=self.intent_ttl_seconds,
        )
        try:
            await transaction.execute()
        except RedisError:
            await self.delete(intent.intent_id, intent.idempotency_key)
            raise

    async def get(self, intent_id: str) -> OrderIntent | None:
        payload = await self.redis.get(self._intent_key(intent_id))
        return None if payload is None else self._deserialize(payload)

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> OrderIntent | None:
        intent_id = await self.redis.get(self._idempotency_key(idempotency_key))
        if intent_id is None:
            return None
        if isinstance(intent_id, bytes):
            intent_id = intent_id.decode()
        return await self.get(cast(str, intent_id))

    async def delete(self, intent_id: str, idempotency_key: str) -> None:
        await self.redis.delete(
            self._intent_key(intent_id), self._idempotency_key(idempotency_key)
        )
