from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime

from app.core.config import Settings, get_settings
from app.services.broker_events.models import (
    BrokerEvent,
    BrokerEventProcessingResult,
    BrokerEventType,
    BrokerExecutionPayload,
    BrokerOrderStatusPayload,
)
from app.services.broker_events.store import BrokerEventStore, DuplicateBrokerEventError
from app.services.order_execution import (
    ExecutionStatus,
    ExecutionUpdate,
    InvalidExecutionTransitionError,
    OrderExecution,
    OrderExecutionNotFoundError,
    OrderExecutionStateMachine,
    PaperOrderExecutionService,
)
from app.services.positions import (
    DuplicateExecutionFillError,
    ExecutionFill,
    PaperPositionService,
)

# Standard US equity option contract size.
OPTION_MULTIPLIER = 100

# Broker order statuses that move an execution, and the status they move it to. FILLED is
# left to execution reports, which carry the fill quantities and prices.
_STATUS_TARGETS: dict[str, ExecutionStatus] = {
    "PRE_SUBMITTED": "ACKNOWLEDGED",
    "SUBMITTED": "ACKNOWLEDGED",
    "PENDING_CANCEL": "CANCEL_PENDING",
    "CANCELLED": "CANCELLED",
    "API_CANCELLED": "CANCELLED",
    "INACTIVE": "REJECTED",
}


class BrokerEventService:
    """Applies broker callbacks to executions and positions, once per event.

    An execution report (IBKR execDetails) advances the execution's filled quantity and
    books the fill into the position, which also records realized P&L for the day. An order
    status callback moves the execution through acknowledgement, cancellation or rejection.
    Each event is stored with an idempotency key, so a replayed callback changes nothing.
    """

    def __init__(
        self,
        store: BrokerEventStore,
        executions: PaperOrderExecutionService,
        positions: PaperPositionService,
        settings: Settings | None = None,
    ) -> None:
        self.store = store
        self.executions = executions
        self.positions = positions
        self.settings = settings or get_settings()

    @staticmethod
    def _event_id(idempotency_key: str) -> str:
        return f"broker_event_{hashlib.sha256(idempotency_key.encode()).hexdigest()[:24]}"

    async def _receive(
        self,
        event_type: BrokerEventType,
        idempotency_key: str,
        broker_order_id: str,
        payload: BrokerExecutionPayload | BrokerOrderStatusPayload,
    ) -> BrokerEvent | None:
        event_id = self._event_id(idempotency_key)
        try:
            await self.store.reserve(idempotency_key, event_id)
        except DuplicateBrokerEventError:
            return None
        now = datetime.now(UTC)
        event = BrokerEvent(
            event_id=event_id,
            idempotency_key=idempotency_key,
            event_type=event_type,
            status="PROCESSING",
            broker="IBKR",
            trading_mode="paper",
            broker_order_id=broker_order_id,
            execution_id=None,
            payload=payload,
            attempt_count=1,
            max_attempts=self.settings.worker_max_retries,
            received_at=now,
            processing_started_at=now,
            processed_at=None,
            created_at=now,
            updated_at=now,
            error_type=None,
            error_message=None,
            retryable=False,
        )
        await self.store.save(event)
        return event

    async def _finish(
        self,
        event: BrokerEvent,
        execution: OrderExecution | None,
        status: str,
        message: str,
        *,
        position_required: bool = False,
        error: Exception | None = None,
    ) -> BrokerEventProcessingResult:
        now = datetime.now(UTC)
        finished = replace(
            event,
            status=status,
            execution_id=execution.execution_id if execution else event.execution_id,
            processed_at=now if status in {"PROCESSED", "SKIPPED"} else None,
            updated_at=now,
            error_type=type(error).__name__ if error else None,
            error_message=str(error) if error else None,
            retryable=status == "FAILED",
        )
        await self.store.save(finished)
        return BrokerEventProcessingResult(
            event=finished,
            execution_id=finished.execution_id,
            execution_status=execution.status if execution else None,
            position_reconciliation_required=position_required,
            message=message,
        )

    async def _duplicate(self, idempotency_key: str) -> BrokerEventProcessingResult:
        existing = await self.store.get_by_idempotency_key(idempotency_key)
        if existing is None:
            raise DuplicateBrokerEventError("This broker event is already being processed.")
        return BrokerEventProcessingResult(
            event=existing,
            execution_id=existing.execution_id,
            execution_status=None,
            position_reconciliation_required=False,
            message="Duplicate broker event; already received.",
        )

    async def ingest_execution(self, payload: BrokerExecutionPayload) -> BrokerEventProcessingResult:
        key = f"EXECUTION_DETAILS:{payload.execution_id}"
        event = await self._receive("EXECUTION_DETAILS", key, payload.broker_order_id, payload)
        if event is None:
            return await self._duplicate(key)
        return await self._process(event)

    async def ingest_order_status(
        self, payload: BrokerOrderStatusPayload
    ) -> BrokerEventProcessingResult:
        key = (
            f"ORDER_STATUS:{payload.broker_order_id}:{payload.normalized_status}:"
            f"{payload.filled_quantity}"
        )
        event = await self._receive("ORDER_STATUS", key, payload.broker_order_id, payload)
        if event is None:
            return await self._duplicate(key)
        return await self._process(event)

    async def get(self, event_id: str) -> BrokerEvent | None:
        return await self.store.get(event_id)

    async def retry_failed_for_broker_order(self, broker_order_id: str) -> int:
        """Reprocess this order's FAILED events; returns how many were retried."""
        retried = 0
        event_ids = await self.store.list_ids_for_broker_order(
            broker_order_id, limit=self.settings.broker_event_batch_size
        )
        for event_id in event_ids:
            event = await self.store.get(event_id)
            if event is None or event.status != "FAILED":
                continue
            retried += 1
            if event.attempt_count >= event.max_attempts:
                await self._finish(
                    event, None, "DEAD_LETTER", "Retries exhausted.",
                    error=RuntimeError(event.error_message or "Retries exhausted."),
                )
                continue
            now = datetime.now(UTC)
            attempt = replace(
                event, status="PROCESSING", attempt_count=event.attempt_count + 1,
                processing_started_at=now, updated_at=now,
            )
            await self.store.save(attempt)
            await self._process(attempt)
        return retried

    async def _process(self, event: BrokerEvent) -> BrokerEventProcessingResult:
        if isinstance(event.payload, BrokerExecutionPayload):
            return await self._apply_execution(event, event.payload)
        if isinstance(event.payload, BrokerOrderStatusPayload):
            return await self._apply_order_status(event, event.payload)
        return await self._finish(event, None, "SKIPPED", "Event type is not applied.")

    async def _apply_execution(
        self, event: BrokerEvent, payload: BrokerExecutionPayload
    ) -> BrokerEventProcessingResult:
        execution: OrderExecution | None = None
        try:
            execution = await self.executions.get_by_broker_order_id(payload.broker_order_id)
            if payload.side != execution.side or payload.option_symbol != execution.option_symbol:
                raise ValueError("Execution report contract or side does not match the order.")
            execution = await self._advance_fill(execution, payload)
            fill = ExecutionFill(
                fill_id=payload.execution_id,
                execution_id=execution.execution_id,
                broker_order_id=execution.broker_order_id,
                account_id=payload.account_id,
                symbol=payload.symbol,
                option_symbol=payload.option_symbol,
                side=payload.side,
                quantity=int(payload.quantity),
                fill_price=payload.fill_price,
                multiplier=OPTION_MULTIPLIER,
                filled_at=payload.execution_time,
            )
            try:
                await self.positions.process_fill(fill, execution)
            except DuplicateExecutionFillError:
                pass
        except OrderExecutionNotFoundError as exc:
            # The callback can arrive before the order is linked to its broker ID; retry later.
            return await self._finish(event, None, "FAILED", str(exc), error=exc)
        except (ValueError, InvalidExecutionTransitionError) as exc:
            return await self._finish(event, execution, "DEAD_LETTER", str(exc), error=exc)
        except RuntimeError as exc:
            return await self._finish(
                event, execution, "FAILED", str(exc), position_required=True, error=exc
            )
        return await self._finish(event, execution, "PROCESSED", "Fill applied to the position.")

    async def _advance_fill(
        self, execution: OrderExecution, payload: BrokerExecutionPayload
    ) -> OrderExecution:
        cumulative = int(payload.cumulative_quantity)
        if cumulative <= 0 or cumulative > execution.requested_quantity:
            raise ValueError("Cumulative fill quantity is outside the order quantity.")
        if cumulative <= execution.filled_quantity:
            # Already reflected, e.g. a replay after the position update failed.
            return execution
        status: ExecutionStatus = (
            "FILLED" if cumulative == execution.requested_quantity else "PARTIALLY_FILLED"
        )
        return await self.executions.apply_update(
            execution.execution_id,
            ExecutionUpdate(
                status=status,
                broker_status="Filled" if status == "FILLED" else "PartiallyFilled",
                filled_quantity=cumulative,
                remaining_quantity=execution.requested_quantity - cumulative,
                average_fill_price=payload.average_price,
            ),
        )

    async def _apply_order_status(
        self, event: BrokerEvent, payload: BrokerOrderStatusPayload
    ) -> BrokerEventProcessingResult:
        try:
            execution = await self.executions.get_by_broker_order_id(payload.broker_order_id)
        except OrderExecutionNotFoundError as exc:
            return await self._finish(event, None, "FAILED", str(exc), error=exc)
        target = _STATUS_TARGETS.get(payload.normalized_status)
        if (
            target == "CANCELLED"
            and not OrderExecutionStateMachine.can_transition(execution.status, target)
            and OrderExecutionStateMachine.can_transition(execution.status, "CANCEL_PENDING")
        ):
            # A cancel the broker started itself (e.g. an expired order) skips our request.
            execution = await self.executions.apply_update(
                execution.execution_id,
                ExecutionUpdate(status="CANCEL_PENDING", broker_status=payload.broker_status),
            )
        if target is None or target == execution.status or not (
            OrderExecutionStateMachine.can_transition(execution.status, target)
        ):
            return await self._finish(
                event, execution, "SKIPPED",
                f"Status {payload.normalized_status} does not change a {execution.status} order.",
            )
        updated = await self.executions.apply_update(
            execution.execution_id,
            ExecutionUpdate(
                status=target,
                broker_status=payload.broker_status,
                status_reason=payload.why_held,
            ),
        )
        return await self._finish(event, updated, "PROCESSED", f"Order moved to {target}.")
