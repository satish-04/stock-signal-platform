from datetime import datetime
from typing import Protocol


class StatusCandidateIndex(Protocol):
    async def list_ids_by_statuses(
        self, statuses: tuple[str, ...], *, limit: int
    ) -> list[str]: ...

    async def list_ids_updated_before(
        self, statuses: tuple[str, ...], *, updated_before: datetime, limit: int
    ) -> list[str]: ...


class AccountRegistry(Protocol):
    async def list_account_ids(self, *, limit: int) -> list[str]: ...
