from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

from app.core.config import Settings, get_settings
from app.services.brokers.base import BrokerAdapter
from app.services.order_execution.models import ExecutionUpdate, OrderExecution
from app.services.order_execution.state_machine import OrderExecutionStateMachine
from app.services.order_execution.store import (
    OrderExecutionNotFoundError,
    OrderExecutionStore,
)
from app.services.order_intents.models import OrderIntent

ZERO = Decimal(0)


class ExecutionIntentRejectedError(RuntimeError):
    """Raised when an order intent cannot create an execution."""


class ExecutionSubmissionDisabledError(PermissionError):
    """Raised when paper submission is disabled."""


class ExecutionLiveTradingBlockedError(PermissionError):
    """Raised when execution is attempted outside paper mode."""


class ExecutionCancellationError(RuntimeError):
    """Raised when cancellation cannot be requested."""


class PaperOrderExecutionService:
    def __init__(
        self,
        broker: BrokerAdapter,
        store: OrderExecutionStore,
        settings: Settings | None = None,
    ) -> None:
        self.broker = broker
        self.store = store
        self.settings = settings or get_settings()

    @staticmethod
    def _execution_id(intent: OrderIntent) -> str:
        digest = hashlib.sha256(intent.intent_id.encode()).hexdigest()
        return f"execution_{digest[:24]}"

    @staticmethod
    def _validate_intent(intent: OrderIntent) -> None:
        if intent.status != "APPROVED":
            raise ExecutionIntentRejectedError(
                "Only APPROVED order intents may create executions."
            )
        if intent.rejection_reasons:
            raise ExecutionIntentRejectedError(
                "Approved order intent contains rejection reasons."
            )
        if intent.quantity <= 0 or intent.limit_price <= ZERO:
            raise ExecutionIntentRejectedError(
                "Order intent quantity and limit price must be greater than zero."
            )

    async def create(self, intent: OrderIntent) -> OrderExecution:
        self._validate_intent(intent)
        execution_id = self._execution_id(intent)
        await self.store.reserve(intent.intent_id, execution_id)
        now = datetime.now(UTC)
        execution = OrderExecution(
            execution_id=execution_id,
            intent_id=intent.intent_id,
            idempotency_key=intent.idempotency_key,
            symbol=intent.symbol,
            option_symbol=intent.option_symbol,
            side=intent.side,
            order_type=intent.order_type,
            requested_quantity=intent.quantity,
            limit_price=intent.limit_price,
            status="CREATED",
            broker_order_id=None,
            broker_status=None,
            filled_quantity=0,
            remaining_quantity=intent.quantity,
            average_fill_price=None,
            submitted_at=None,
            acknowledged_at=None,
            completed_at=None,
            created_at=now,
            updated_at=now,
            status_reason=None,
            broker_response=None,
        )
        await self.store.save(execution)
        return execution

    async def get(self, execution_id: str) -> OrderExecution:
        execution = await self.store.get(execution_id.strip())
        if execution is None:
            raise OrderExecutionNotFoundError(f"Execution {execution_id!r} was not found.")
        return execution

    async def get_by_intent_id(self, intent_id: str) -> OrderExecution:
        execution = await self.store.get_by_intent_id(intent_id.strip())
        if execution is None:
            raise OrderExecutionNotFoundError(
                f"No execution exists for intent {intent_id!r}."
            )
        return execution

    async def get_by_broker_order_id(self, broker_order_id: str) -> OrderExecution:
        execution = await self.store.get_by_broker_order_id(broker_order_id.strip())
        if execution is None:
            raise OrderExecutionNotFoundError(
                "No execution exists for the supplied broker order ID."
            )
        return execution

    async def apply_update(
        self, execution_id: str, update: ExecutionUpdate
    ) -> OrderExecution:
        execution = await self.get(execution_id)
        OrderExecutionStateMachine.validate_transition(execution.status, update.status)
        filled = execution.filled_quantity if update.filled_quantity is None else update.filled_quantity
        remaining = (
            execution.remaining_quantity
            if update.remaining_quantity is None
            else update.remaining_quantity
        )
        if filled < 0 or remaining < 0 or filled + remaining > execution.requested_quantity:
            raise ValueError("Invalid filled and remaining quantities.")
        if update.status == "FILLED":
            filled, remaining = execution.requested_quantity, 0
        now = datetime.now(UTC)
        submitted_at = execution.submitted_at
        acknowledged_at = execution.acknowledged_at
        completed_at = execution.completed_at
        if update.status == "SUBMITTED" and submitted_at is None:
            submitted_at = now
        if update.status == "ACKNOWLEDGED" and acknowledged_at is None:
            acknowledged_at = now
        if OrderExecutionStateMachine.is_terminal(update.status):
            completed_at = now
        updated = replace(
            execution,
            status=update.status,
            broker_order_id=update.broker_order_id or execution.broker_order_id,
            broker_status=update.broker_status or execution.broker_status,
            filled_quantity=filled,
            remaining_quantity=remaining,
            average_fill_price=update.average_fill_price or execution.average_fill_price,
            submitted_at=submitted_at,
            acknowledged_at=acknowledged_at,
            completed_at=completed_at,
            updated_at=now,
            status_reason=update.status_reason,
            broker_response=update.broker_response or execution.broker_response,
        )
        await self.store.save(updated)
        return updated

    def _validate_submission_safety(self) -> None:
        if self.settings.trading_mode != "paper":
            raise ExecutionLiveTradingBlockedError(
                "Execution submission is restricted to paper mode."
            )
        if not self.settings.enable_order_submission:
            raise ExecutionSubmissionDisabledError("Order submission is disabled.")

    async def submit(self, execution_id: str) -> OrderExecution:
        self._validate_submission_safety()
        execution = await self.apply_update(
            execution_id, ExecutionUpdate(status="SUBMISSION_PENDING")
        )
        response = await self.broker.submit_order(
            {
                "execution_id": execution.execution_id,
                "intent_id": execution.intent_id,
                "idempotency_key": execution.idempotency_key,
                "symbol": execution.symbol,
                "option_symbol": execution.option_symbol,
                "side": execution.side,
                "order_type": execution.order_type,
                "quantity": execution.requested_quantity,
                "limit_price": str(execution.limit_price),
                "transmit": False,
                "trading_mode": "paper",
            }
        )
        broker_order_id = str(
            response.get("broker_order_id") or f"paper-{execution.execution_id}"
        )
        return await self.apply_update(
            execution_id,
            ExecutionUpdate(
                status="SUBMITTED",
                broker_order_id=broker_order_id,
                broker_status=str(response.get("status", "submitted")),
                broker_response=response,
            ),
        )

    async def cancel(self, execution_id: str) -> OrderExecution:
        self._validate_submission_safety()
        execution = await self.get(execution_id)
        if not execution.broker_order_id:
            raise ExecutionCancellationError("Execution has no broker order ID.")
        pending = await self.apply_update(
            execution_id, ExecutionUpdate(status="CANCEL_PENDING")
        )
        response = await self.broker.cancel_order(
            {
                "execution_id": pending.execution_id,
                "broker_order_id": pending.broker_order_id,
                "transmit": False,
                "trading_mode": "paper",
            }
        )
        return await self.apply_update(
            execution_id,
            ExecutionUpdate(
                status="CANCELLED",
                broker_status=str(response.get("status", "cancelled")),
                broker_response=response,
            ),
        )
