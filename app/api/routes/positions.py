from datetime import datetime
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.positions import (
    Position,
    PositionAccountingError,
    PositionNotFoundError,
    get_position_service,
)

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])


class PositionResponse(BaseModel):
    position_id: str
    account_id: str
    symbol: str
    option_symbol: str
    side: Literal["LONG", "SHORT"]
    status: Literal["OPEN", "CLOSED"]
    quantity: int
    multiplier: int
    average_entry_price: Decimal
    current_mark_price: Decimal | None
    cost_basis: Decimal
    market_value: Decimal | None
    realized_pnl: Decimal
    unrealized_pnl: Decimal | None
    opened_at: datetime
    updated_at: datetime
    closed_at: datetime | None


class PositionListResponse(BaseModel):
    account_id: str
    count: int
    items: list[PositionResponse]


class MarkPositionRequest(BaseModel):
    mark_price: Decimal = Field(gt=0)


class PortfolioSummaryResponse(BaseModel):
    account_id: str
    open_positions: int
    closed_positions: int
    total_positions: int
    total_cost_basis: Decimal
    total_market_value: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_pnl: Decimal


def _response(position: Position) -> PositionResponse:
    return PositionResponse(**position.__dict__)


@router.get("", response_model=PositionListResponse)
async def list_positions(
    account_id: str = Query(min_length=1, max_length=128),
    status: Literal["OPEN", "CLOSED"] | None = None,
) -> PositionListResponse:
    positions = await get_position_service().list_positions(account_id, status=status)
    return PositionListResponse(
        account_id=account_id,
        count=len(positions),
        items=[_response(position) for position in positions],
    )


@router.get("/by-contract/{account_id}", response_model=PositionResponse)
async def get_position_by_contract(
    account_id: str,
    option_symbol: str = Query(min_length=1, max_length=128),
) -> PositionResponse:
    try:
        return _response(
            await get_position_service().get_by_contract(account_id, option_symbol)
        )
    except PositionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/portfolio/{account_id}/summary", response_model=PortfolioSummaryResponse)
async def portfolio_summary(account_id: str) -> PortfolioSummaryResponse:
    summary = await get_position_service().portfolio_summary(account_id)
    realized = summary["realized_pnl"]
    unrealized = summary["unrealized_pnl"]
    return PortfolioSummaryResponse(
        account_id=account_id,
        **summary,
        total_pnl=realized + unrealized,
    )


@router.get("/{position_id}", response_model=PositionResponse)
async def get_position(position_id: str) -> PositionResponse:
    try:
        return _response(await get_position_service().get(position_id))
    except PositionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{position_id}/mark", response_model=PositionResponse)
async def mark_position(
    position_id: str, payload: MarkPositionRequest
) -> PositionResponse:
    try:
        return _response(
            await get_position_service().update_mark(position_id, payload.mark_price)
        )
    except PositionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (PositionAccountingError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
