from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.position_exits import (
    DuplicatePositionExitError,
    PositionExitContext,
    PositionExitSignal,
    PositionExitSignalNotFoundError,
    get_position_exit_service,
)

router = APIRouter(prefix="/api/v1/position-exits", tags=["position-exits"])


class MonitorRequest(BaseModel):
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    quantity: int = Field(gt=0)
    multiplier: int = Field(gt=0)
    average_entry_price: Decimal = Field(gt=0)
    current_mark_price: Decimal = Field(gt=0)
    highest_mark_price: Decimal = Field(gt=0)
    opened_at: datetime
    evaluated_at: datetime
    mark_updated_at: datetime
    expiration: datetime | None = None
    first_target_already_taken: bool = False


class ExitSignalResponse(BaseModel):
    exit_signal_id: str
    idempotency_key: str
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    reason: str
    urgency: str
    status: str
    requested_quantity: int
    mark_price: Decimal
    trigger_price: Decimal | None
    created_at: datetime
    updated_at: datetime
    explanations: list[str]
    rejection_reasons: list[str]


def _response(signal: PositionExitSignal) -> ExitSignalResponse:
    data = dict(signal.__dict__)
    data["explanations"] = list(signal.explanations)
    data["rejection_reasons"] = list(signal.rejection_reasons)
    return ExitSignalResponse(**data)


@router.post("/monitor", response_model=ExitSignalResponse | None)
async def monitor_position(payload: MonitorRequest) -> ExitSignalResponse | None:
    try:
        signal = await get_position_exit_service().monitor(
            PositionExitContext(**payload.model_dump())
        )
        return None if signal is None else _response(signal)
    except DuplicatePositionExitError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{signal_id}", response_model=ExitSignalResponse)
async def get_signal(signal_id: str) -> ExitSignalResponse:
    try:
        return _response(await get_position_exit_service().get(signal_id))
    except PositionExitSignalNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/by-position/{position_id}", response_model=list[ExitSignalResponse])
async def list_signals(position_id: str) -> list[ExitSignalResponse]:
    return [
        _response(signal)
        for signal in await get_position_exit_service().list_for_position(position_id)
    ]
