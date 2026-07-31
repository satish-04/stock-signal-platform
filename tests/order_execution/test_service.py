from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.core.config import Settings
from app.services.order_execution import (
    DuplicateOrderExecutionError,
    ExecutionIntentRejectedError,
    ExecutionSubmissionDisabledError,
    ExecutionUpdate,
    InMemoryOrderExecutionStore,
    PaperOrderExecutionService,
)
from app.services.order_intents import OrderIntent


class Broker:
    async def submit_order(self, order: dict) -> dict:
        return {"status": "simulated", "broker_order_id": "paper-1", "order": order}

    async def cancel_order(self, order: dict) -> dict:
        return {"status": "cancelled", "broker_order_id": "paper-1", "order": order}


def settings(enabled: bool = False) -> Settings:
    return Settings(
        tradingview_webhook_secret="test-webhook-secret-123456",
        enable_order_submission=enabled,
    )


def intent() -> OrderIntent:
    return OrderIntent(
        intent_id="intent-1",
        idempotency_key="idem-1",
        symbol="AAPL",
        option_symbol="AAPL-CALL",
        side="BUY",
        order_type="LIMIT",
        quantity=2,
        limit_price=Decimal("5.00"),
        estimated_debit=Decimal(1000),
        maximum_loss=Decimal(1000),
        stop_price=Decimal(4),
        first_target_price=Decimal(7),
        second_target_price=Decimal(9),
        status="APPROVED",
        created_at=datetime.now(UTC),
        reasons=("approved",),
        rejection_reasons=(),
    )


def service(enabled: bool = False) -> PaperOrderExecutionService:
    return PaperOrderExecutionService(
        Broker(), InMemoryOrderExecutionStore(), settings(enabled)
    )


@pytest.mark.asyncio
async def test_create_and_retrieve_execution() -> None:
    subject = service()
    created = await subject.create(intent())
    assert created.status == "CREATED"
    assert created.remaining_quantity == 2
    assert await subject.get(created.execution_id) == created
    assert await subject.get_by_intent_id(created.intent_id) == created


@pytest.mark.asyncio
async def test_duplicate_intent_execution_is_rejected() -> None:
    subject = service()
    await subject.create(intent())
    with pytest.raises(DuplicateOrderExecutionError):
        await subject.create(intent())


@pytest.mark.asyncio
async def test_non_approved_intent_is_rejected() -> None:
    with pytest.raises(ExecutionIntentRejectedError):
        await service().create(replace(intent(), status="REJECTED"))


@pytest.mark.asyncio
async def test_submission_disabled_by_default() -> None:
    subject = service()
    execution = await subject.create(intent())
    with pytest.raises(ExecutionSubmissionDisabledError):
        await subject.submit(execution.execution_id)


@pytest.mark.asyncio
async def test_submit_and_cancel_paper_order() -> None:
    subject = service(True)
    execution = await subject.create(intent())
    submitted = await subject.submit(execution.execution_id)
    assert submitted.status == "SUBMITTED"
    assert submitted.broker_order_id == "paper-1"
    assert submitted.broker_response["order"]["transmit"] is False
    cancelled = await subject.cancel(execution.execution_id)
    assert cancelled.status == "CANCELLED"
    assert cancelled.completed_at is not None


@pytest.mark.asyncio
async def test_fill_update_sets_quantities_and_completion() -> None:
    subject = service(True)
    execution = await subject.create(intent())
    submitted = await subject.submit(execution.execution_id)
    filled = await subject.apply_update(
        submitted.execution_id,
        ExecutionUpdate(status="FILLED", average_fill_price=Decimal("4.95")),
    )
    assert filled.filled_quantity == 2
    assert filled.remaining_quantity == 0
    assert filled.completed_at is not None
