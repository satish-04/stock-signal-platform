from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.trade_risk import RiskLimits, TradeConstructionRequest, TradeRiskEngine

router = APIRouter(prefix="/api/v1/risk", tags=["trade-risk"])


class RiskLimitsRequest(BaseModel):
    account_equity: Decimal = Field(gt=0)
    available_funds: Decimal = Field(ge=0)
    max_risk_per_trade_pct: Decimal = Field(gt=0, le=100)
    max_position_value_pct: Decimal = Field(gt=0, le=100)
    max_contracts: int = Field(gt=0)
    max_bid_ask_spread_pct: Decimal = Field(ge=0)
    minimum_open_interest: int = Field(ge=0)
    minimum_volume: int = Field(ge=0)
    minimum_reward_risk_ratio: Decimal = Field(gt=0)


class TradePlanRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    option_symbol: str = Field(min_length=1, max_length=64)
    option_type: Literal["CALL", "PUT"]
    expiry: str = Field(min_length=8, max_length=10)
    strike: Decimal = Field(gt=0)
    multiplier: int = Field(default=100, gt=0)
    bid: Decimal = Field(ge=0)
    ask: Decimal = Field(gt=0)
    last: Decimal = Field(ge=0)
    volume: int = Field(ge=0)
    open_interest: int = Field(ge=0)
    action: Literal["BUY_CALL", "BUY_PUT", "HOLD"]
    confidence: Decimal = Field(ge=0, le=100)
    stop_loss_pct: Decimal = Field(gt=0, lt=100)
    first_target_pct: Decimal = Field(gt=0)
    second_target_pct: Decimal = Field(gt=0)
    limits: RiskLimitsRequest


class TradePlanResponse(BaseModel):
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


@router.post("/trade-plan", response_model=TradePlanResponse)
async def construct_trade_plan(payload: TradePlanRequest) -> TradePlanResponse:
    request = TradeConstructionRequest(
        symbol=payload.symbol,
        option_symbol=payload.option_symbol,
        option_type=payload.option_type,
        expiry=payload.expiry,
        strike=payload.strike,
        multiplier=payload.multiplier,
        bid=payload.bid,
        ask=payload.ask,
        last=payload.last,
        volume=payload.volume,
        open_interest=payload.open_interest,
        action=payload.action,
        confidence=payload.confidence,
        stop_loss_pct=payload.stop_loss_pct,
        first_target_pct=payload.first_target_pct,
        second_target_pct=payload.second_target_pct,
    )
    limits = RiskLimits(
        account_equity=payload.limits.account_equity,
        available_funds=payload.limits.available_funds,
        max_risk_per_trade_pct=payload.limits.max_risk_per_trade_pct,
        max_position_value_pct=payload.limits.max_position_value_pct,
        max_contracts=payload.limits.max_contracts,
        max_bid_ask_spread_pct=payload.limits.max_bid_ask_spread_pct,
        minimum_open_interest=payload.limits.minimum_open_interest,
        minimum_volume=payload.limits.minimum_volume,
        minimum_reward_risk_ratio=payload.limits.minimum_reward_risk_ratio,
    )
    try:
        plan = TradeRiskEngine.construct(request=request, limits=limits)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return TradePlanResponse(
        symbol=plan.symbol,
        option_symbol=plan.option_symbol,
        decision=plan.decision,
        side=plan.side,
        order_type=plan.order_type,
        quantity=plan.quantity,
        limit_price=plan.limit_price,
        estimated_debit=plan.estimated_debit,
        maximum_loss=plan.maximum_loss,
        stop_price=plan.stop_price,
        first_target_price=plan.first_target_price,
        second_target_price=plan.second_target_price,
        reward_risk_ratio=plan.reward_risk_ratio,
        account_risk_pct=plan.account_risk_pct,
        bid_ask_spread_pct=plan.bid_ask_spread_pct,
        reasons=list(plan.reasons),
        rejection_reasons=list(plan.rejection_reasons),
    )
