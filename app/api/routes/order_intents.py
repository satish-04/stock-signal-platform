from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.brokers.factory import get_broker
from app.services.order_intents import (
    DuplicateOrderIntentError,
    LiveTradingBlockedError,
    OrderIntentRejectedError,
    OrderSubmissionDisabledError,
    PaperOrderApprovalService,
)
from app.services.trade_risk import TradePlan

router = APIRouter(prefix="/api/v1/order-intents", tags=["order-intents"])


class OrderIntentTradePlanRequest(BaseModel):
    symbol: str
    option_symbol: str
    decision: Literal["APPROVED", "REJECTED"]
    side: Literal["BUY", "SELL"]
    order_type: Literal["LIMIT"]
    quantity: int
    limit_price: Decimal
    estimated_debit: Decimal
    maximum_loss: Decimal
    stop_price: Decimal
    first_target_price: Decimal
    second_target_price: Decimal
    reward_risk_ratio: Decimal
    account_risk_pct: Decimal
    bid_ask_spread_pct: Decimal
    reasons: list[str]
    rejection_reasons: list[str]


class OrderIntentResponse(BaseModel):
    intent_id: str
    idempotency_key: str
    status: str
    symbol: str
    option_symbol: str
    side: str
    order_type: str
    quantity: int
    limit_price: Decimal
    broker_response: dict | None


def _to_trade_plan(payload: OrderIntentTradePlanRequest) -> TradePlan:
    data = payload.model_dump()
    data["reasons"] = tuple(data["reasons"])
    data["rejection_reasons"] = tuple(data["rejection_reasons"])
    return TradePlan(**data)


def _response(intent, broker_response: dict | None = None) -> OrderIntentResponse:
    return OrderIntentResponse(
        intent_id=intent.intent_id,
        idempotency_key=intent.idempotency_key,
        status=intent.status,
        symbol=intent.symbol,
        option_symbol=intent.option_symbol,
        side=intent.side,
        order_type=intent.order_type,
        quantity=intent.quantity,
        limit_price=intent.limit_price,
        broker_response=broker_response,
    )


@router.post("", response_model=OrderIntentResponse)
async def create_order_intent(
    payload: OrderIntentTradePlanRequest,
) -> OrderIntentResponse:
    try:
        intent = PaperOrderApprovalService(get_broker()).create_intent(
            _to_trade_plan(payload)
        )
    except OrderIntentRejectedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DuplicateOrderIntentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _response(intent)


@router.post("/submit", response_model=OrderIntentResponse)
async def submit_order_intent(
    payload: OrderIntentTradePlanRequest,
) -> OrderIntentResponse:
    try:
        result = await PaperOrderApprovalService(get_broker()).submit(
            _to_trade_plan(payload)
        )
    except OrderIntentRejectedError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except DuplicateOrderIntentError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except (OrderSubmissionDisabledError, LiveTradingBlockedError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return _response(result.intent, result.broker_response)
