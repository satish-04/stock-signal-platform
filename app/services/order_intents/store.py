from __future__ import annotations

from threading import Lock


class DuplicateOrderIntentError(RuntimeError):
    """Raised when an idempotency key has already been registered."""


class InMemoryOrderIntentStore:
    def __init__(self) -> None:
        self._keys: set[str] = set()
        self._lock = Lock()

    def contains(self, idempotency_key: str) -> bool:
        with self._lock:
            return idempotency_key in self._keys

    def register(self, idempotency_key: str) -> None:
        with self._lock:
            if idempotency_key in self._keys:
                raise DuplicateOrderIntentError(
                    "An order intent with this idempotency key has already been registered."
                )
            self._keys.add(idempotency_key)

    def clear(self) -> None:
        with self._lock:
            self._keys.clear()
