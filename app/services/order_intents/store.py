from __future__ import annotations

import asyncio
from typing import Protocol

from app.services.order_intents.models import OrderIntent


class DuplicateOrderIntentError(RuntimeError):
    """Raised when an idempotency key is already reserved."""


class OrderIntentNotFoundError(LookupError):
    """Raised when an order-intent record does not exist."""


class OrderIntentStore(Protocol):
    async def reserve(self, idempotency_key: str, intent_id: str) -> None: ...

    async def save(self, intent: OrderIntent) -> None: ...

    async def get(self, intent_id: str) -> OrderIntent | None: ...

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> OrderIntent | None: ...

    async def delete(self, intent_id: str, idempotency_key: str) -> None: ...


class InMemoryOrderIntentStore:
    def __init__(self) -> None:
        self._intent_ids_by_key: dict[str, str] = {}
        self._intents: dict[str, OrderIntent] = {}
        self._lock = asyncio.Lock()

    async def reserve(self, idempotency_key: str, intent_id: str) -> None:
        async with self._lock:
            if idempotency_key in self._intent_ids_by_key:
                raise DuplicateOrderIntentError(
                    "An order intent with this idempotency key "
                    "has already been registered."
                )
            self._intent_ids_by_key[idempotency_key] = intent_id

    async def save(self, intent: OrderIntent) -> None:
        async with self._lock:
            self._intents[intent.intent_id] = intent
            self._intent_ids_by_key[intent.idempotency_key] = intent.intent_id

    async def get(self, intent_id: str) -> OrderIntent | None:
        async with self._lock:
            return self._intents.get(intent_id)

    async def get_by_idempotency_key(
        self, idempotency_key: str
    ) -> OrderIntent | None:
        async with self._lock:
            intent_id = self._intent_ids_by_key.get(idempotency_key)
            return None if intent_id is None else self._intents.get(intent_id)

    async def delete(self, intent_id: str, idempotency_key: str) -> None:
        async with self._lock:
            self._intents.pop(intent_id, None)
            self._intent_ids_by_key.pop(idempotency_key, None)

    async def clear(self) -> None:
        async with self._lock:
            self._intents.clear()
            self._intent_ids_by_key.clear()

    async def contains(self, idempotency_key: str) -> bool:
        async with self._lock:
            return idempotency_key in self._intent_ids_by_key

    async def register(self, idempotency_key: str) -> None:
        await self.reserve(idempotency_key, f"legacy_{idempotency_key}")
