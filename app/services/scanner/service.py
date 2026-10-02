import asyncio
import time
from collections.abc import Callable
from datetime import date, datetime, timezone
from typing import Any, Protocol
from uuid import UUID

import structlog

from app.db.session import SessionLocal
from app.models.entities import OptionsScan
from app.services.scanner.engine import (
    MARKET_TIMEZONE,
    ChainSnapshot,
    OptionsScanEngine,
    upcoming_weekly_expiry,
)
from app.services.scanner.universe import DEFAULT_UNIVERSE
from app.services.scanner.yahoo import YahooOptionsProvider

CONCURRENCY = 5
ATTEMPTS = 3
RETRY_DELAY_SECONDS = 1.5

# Scans running in this process, with their progress. A scan row left in "running" that is
# not listed here was interrupted by a restart.
_active: dict[UUID, dict[str, int]] = {}
_tasks: set[asyncio.Task[None]] = set()


class ChainProvider(Protocol):
    def screen_symbols(self) -> list[str]: ...
    def chain(self, symbol: str, expiry: str) -> ChainSnapshot | None: ...


def market_today() -> date:
    return datetime.now(MARKET_TIMEZONE).date()


def default_expiry() -> date:
    return upcoming_weekly_expiry(datetime.now(timezone.utc))


def is_active(scan_id: UUID) -> bool:
    return scan_id in _active


def progress(scan_id: UUID) -> dict[str, int] | None:
    state = _active.get(scan_id)
    return dict(state) if state else None


async def build_universe(provider: ChainProvider, symbols: list[str] | None) -> list[str]:
    if symbols:
        return list(dict.fromkeys(symbols))
    screened = await asyncio.to_thread(provider.screen_symbols)
    return list(dict.fromkeys([*DEFAULT_UNIVERSE, *screened]))


def _fetch_chain(provider: ChainProvider, symbol: str, expiry: str) -> ChainSnapshot | None:
    for attempt in range(1, ATTEMPTS + 1):
        try:
            return provider.chain(symbol, expiry)
        except Exception:
            if attempt == ATTEMPTS:
                raise
            time.sleep(RETRY_DELAY_SECONDS * attempt)
    return None


async def scan_symbols(
    provider: ChainProvider,
    symbols: list[str],
    expiry: str,
    on_progress: Callable[[int], None] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Summarize every symbol's chain. Returns (items by volume, skipped symbols)."""
    engine = OptionsScanEngine()
    now = datetime.now(timezone.utc)
    limiter = asyncio.Semaphore(CONCURRENCY)
    items: list[dict[str, Any]] = []
    skipped: list[dict[str, str]] = []
    done = 0

    async def scan_one(symbol: str) -> None:
        nonlocal done
        async with limiter:
            try:
                chain = await asyncio.to_thread(_fetch_chain, provider, symbol, expiry)
            except Exception as exc:  # noqa: BLE001 - one bad symbol must not fail the scan
                skipped.append({"symbol": symbol, "reason": f"error: {exc}"[:200]})
            else:
                summary = engine.summarize(chain, now) if chain else None
                if summary:
                    items.append(summary)
                else:
                    skipped.append({"symbol": symbol, "reason": "no chain for this expiry"})
        done += 1
        if on_progress:
            on_progress(done)

    await asyncio.gather(*(scan_one(symbol) for symbol in symbols))
    items.sort(key=lambda item: item["total_volume"], reverse=True)
    skipped.sort(key=lambda entry: entry["symbol"])
    return items, skipped


async def _finish(scan_id: UUID, **fields: Any) -> None:
    async with SessionLocal() as session, session.begin():
        scan = await session.get(OptionsScan, scan_id)
        if scan is None:
            return
        for name, value in fields.items():
            setattr(scan, name, value)
        scan.completed_at = datetime.now(timezone.utc)


async def execute_scan(
    scan_id: UUID,
    expiry: date,
    symbols: list[str] | None,
    provider: ChainProvider | None = None,
) -> None:
    log = structlog.get_logger()
    state = _active.setdefault(scan_id, {"done": 0, "total": 0})
    try:
        provider = provider or YahooOptionsProvider()
        universe = await build_universe(provider, symbols)
        state["total"] = len(universe)
        items, skipped = await scan_symbols(
            provider, universe, expiry.isoformat(), lambda done: state.update(done=done)
        )
        engine = OptionsScanEngine()
        traded = [item["last_trade_at"] for item in items if item["last_trade_at"]]
        await _finish(
            scan_id,
            status="completed",
            universe_size=len(universe),
            scanned=len(items),
            skipped=len(skipped),
            result={
                "items": items,
                "top_iv": engine.rank_by_iv(items),
                "iv_min_volume": engine.iv_min_volume(items),
                "skipped": skipped,
                "quotes_as_of": max(traded) if traded else None,
            },
        )
        log.info(
            "options_scan_completed",
            scan_id=str(scan_id),
            expiry=expiry.isoformat(),
            scanned=len(items),
            skipped=len(skipped),
        )
    except Exception as exc:
        log.exception("options_scan_failed", scan_id=str(scan_id))
        await _finish(scan_id, status="failed", error=str(exc)[:500] or type(exc).__name__)
    finally:
        _active.pop(scan_id, None)


def start_scan(scan_id: UUID, expiry: date, symbols: list[str] | None) -> None:
    """Run the scan in the background of the API process."""
    _active[scan_id] = {"done": 0, "total": 0}
    task = asyncio.create_task(execute_scan(scan_id, expiry, symbols))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
