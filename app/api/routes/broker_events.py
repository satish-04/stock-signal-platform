from datetime import UTC, datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.services.broker_events import (
    BrokerEventProcessingResult,
    BrokerExecutionPayload,
    BrokerOrderStatusPayload,
    DuplicateBrokerEventError,
    get_broker_event_service,
    normalize_ibkr_order_status,
)
from app.services.order_execution import OrderExecutionNotFoundError

router = APIRouter(prefix="/api/v1/broker-events", tags=["broker-events"])


class ExecutionReportRequest(BaseModel):
    """An IBKR execDetails callback for a paper order."""

    broker_order_id: str
    execution_id: str = Field(min_length=1, description="The broker's unique execution ID.")
    account_id: str = Field(min_length=1)
    symbol: str
    option_symbol: str
    side: Literal["BUY", "SELL"]
    quantity: Decimal = Field(gt=0)
    fill_price: Decimal = Field(gt=0)
    cumulative_quantity: Decimal = Field(gt=0)
    average_price: Decimal = Field(gt=0)
    execution_time: datetime
    exchange: str | None = None
    permanent_id: str | None = None
    client_id: int | None = None


class OrderStatusRequest(BaseModel):
    """An IBKR orderStatus callback for a paper order."""

    broker_order_id: str
    broker_status: str = Field(description="The raw IBKR status, e.g. Submitted or Cancelled.")
    filled_quantity: Decimal = Field(default=Decimal(0), ge=0)
    remaining_quantity: Decimal = Field(default=Decimal(0), ge=0)
    average_fill_price: Decimal | None = None
    why_held: str | None = None


class SimulatedFillRequest(BaseModel):
    account_id: str = Field(min_length=1)
    quantity: int | None = Field(default=None, gt=0, description="Defaults to the unfilled rest.")
    price: Decimal | None = Field(default=None, gt=0, description="Defaults to the limit price.")


class BrokerEventResponse(BaseModel):
    event_id: str
    event_type: str
    status: str
    broker_order_id: str | None
    execution_id: str | None
    execution_status: str | None
    attempt_count: int
    error_message: str | None
    message: str


def _response(result: BrokerEventProcessingResult) -> BrokerEventResponse:
    event = result.event
    return BrokerEventResponse(
        event_id=event.event_id,
        event_type=event.event_type,
        status=event.status,
        broker_order_id=event.broker_order_id,
        execution_id=result.execution_id,
        execution_status=result.execution_status,
        attempt_count=event.attempt_count,
        error_message=event.error_message,
        message=result.message,
    )


@router.post("/executions", response_model=BrokerEventResponse)
async def ingest_execution(payload: ExecutionReportRequest) -> BrokerEventResponse:
    try:
        result = await get_broker_event_service().ingest_execution(
            BrokerExecutionPayload(**payload.model_dump())
        )
    except DuplicateBrokerEventError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _response(result)


@router.post("/order-status", response_model=BrokerEventResponse)
async def ingest_order_status(payload: OrderStatusRequest) -> BrokerEventResponse:
    data = payload.model_dump()
    try:
        result = await get_broker_event_service().ingest_order_status(
            BrokerOrderStatusPayload(
                **data,
                normalized_status=normalize_ibkr_order_status(payload.broker_status),
                permanent_id=None,
                parent_order_id=None,
                last_fill_price=None,
                client_id=None,
                market_cap_price=None,
            )
        )
    except DuplicateBrokerEventError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _response(result)


@router.get("/{event_id}", response_model=BrokerEventResponse)
async def get_event(event_id: str) -> BrokerEventResponse:
    event = await get_broker_event_service().get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Broker event was not found.")
    return _response(
        BrokerEventProcessingResult(event, event.execution_id, None, False, "")
    )


@router.post("/simulate-fill/{execution_id}", response_model=BrokerEventResponse)
async def simulate_fill(execution_id: str, payload: SimulatedFillRequest) -> BrokerEventResponse:
    """Fill a submitted paper order as the mock broker; only available with mock market data."""
    if get_settings().market_data_mode != "mock":
        raise HTTPException(
            status_code=403, detail="Simulated fills are only available in mock market-data mode."
        )
    service = get_broker_event_service()
    try:
        execution = await service.executions.get(execution_id)
    except OrderExecutionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not execution.broker_order_id:
        raise HTTPException(status_code=409, detail="Submit the order before filling it.")
    quantity = payload.quantity or execution.remaining_quantity
    if quantity <= 0 or quantity > execution.remaining_quantity:
        raise HTTPException(status_code=422, detail="Nothing left to fill, or quantity too large.")
    price = payload.price or execution.limit_price
    cumulative = execution.filled_quantity + quantity
    previous_value = (execution.average_fill_price or Decimal(0)) * execution.filled_quantity
    now = datetime.now(UTC)
    result = await service.ingest_execution(
        BrokerExecutionPayload(
            broker_order_id=execution.broker_order_id,
            execution_id=f"sim-{execution.execution_id}-{cumulative}",
            account_id=payload.account_id,
            symbol=execution.symbol,
            option_symbol=execution.option_symbol,
            side=execution.side,
            quantity=Decimal(quantity),
            fill_price=price,
            cumulative_quantity=Decimal(cumulative),
            average_price=(previous_value + price * quantity) / cumulative,
            exchange="SIMULATED",
            execution_time=now,
            permanent_id=None,
            client_id=None,
        )
    )
    return _response(result)
