from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.brokers.factory import get_broker
from app.services.order_execution import (
    DuplicateOrderExecutionError,
    ExecutionCancellationError,
    ExecutionIntentRejectedError,
    ExecutionLiveTradingBlockedError,
    ExecutionStatus,
    ExecutionSubmissionDisabledError,
    ExecutionUpdate,
    InvalidExecutionTransitionError,
    OrderExecution,
    OrderExecutionNotFoundError,
    get_order_execution_service,
)
from app.services.order_intents.factory import get_order_intent_store

router = APIRouter(prefix="/api/v1/order-executions", tags=["order-executions"])


class ExecutionUpdateRequest(BaseModel):
    status: ExecutionStatus
    broker_order_id: str | None = None
    broker_status: str | None = None
    filled_quantity: int | None = Field(default=None, ge=0)
    remaining_quantity: int | None = Field(default=None, ge=0)
    average_fill_price: Decimal | None = Field(default=None, gt=0)
    status_reason: str | None = None
    broker_response: dict | None = None


class OrderExecutionResponse(BaseModel):
    execution_id: str
    intent_id: str
    idempotency_key: str
    symbol: str
    option_symbol: str
    side: str
    order_type: str
    requested_quantity: int
    limit_price: Decimal
    status: str
    broker_order_id: str | None
    broker_status: str | None
    filled_quantity: int
    remaining_quantity: int
    average_fill_price: Decimal | None
    submitted_at: datetime | None
    acknowledged_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    status_reason: str | None
    broker_response: dict | None


def _response(execution: OrderExecution) -> OrderExecutionResponse:
    return OrderExecutionResponse(**execution.__dict__)


def _service():
    return get_order_execution_service(get_broker())


@router.post("/from-intent/{intent_id}", response_model=OrderExecutionResponse)
async def create_from_intent(intent_id: str) -> OrderExecutionResponse:
    intent = await get_order_intent_store().get(intent_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Order intent was not found.")
    try:
        return _response(await _service().create(intent))
    except ExecutionIntentRejectedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DuplicateOrderExecutionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.get("/{execution_id}", response_model=OrderExecutionResponse)
async def get_execution(execution_id: str) -> OrderExecutionResponse:
    try:
        return _response(await _service().get(execution_id))
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/by-intent/{intent_id}", response_model=OrderExecutionResponse)
async def get_execution_by_intent(intent_id: str) -> OrderExecutionResponse:
    try:
        return _response(await _service().get_by_intent_id(intent_id))
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/by-broker-order/{broker_order_id}", response_model=OrderExecutionResponse)
async def get_execution_by_broker_order(
    broker_order_id: str,
) -> OrderExecutionResponse:
    try:
        return _response(await _service().get_by_broker_order_id(broker_order_id))
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{execution_id}/updates", response_model=OrderExecutionResponse)
async def update_execution(
    execution_id: str, payload: ExecutionUpdateRequest
) -> OrderExecutionResponse:
    try:
        return _response(
            await _service().apply_update(execution_id, ExecutionUpdate(**payload.model_dump()))
        )
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidExecutionTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{execution_id}/submit", response_model=OrderExecutionResponse)
async def submit_execution(execution_id: str) -> OrderExecutionResponse:
    try:
        return _response(await _service().submit(execution_id))
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ExecutionSubmissionDisabledError, ExecutionLiveTradingBlockedError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except InvalidExecutionTransitionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@router.post("/{execution_id}/cancel", response_model=OrderExecutionResponse)
async def cancel_execution(execution_id: str) -> OrderExecutionResponse:
    try:
        return _response(await _service().cancel(execution_id))
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ExecutionSubmissionDisabledError, ExecutionLiveTradingBlockedError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ExecutionCancellationError, InvalidExecutionTransitionError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
