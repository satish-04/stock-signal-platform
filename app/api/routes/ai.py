from __future__ import annotations

from decimal import Decimal
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.ai.service import AIRecommendationService
from app.services.brokers.factory import get_broker

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"],
)


class SelectedOptionResponse(BaseModel):
    symbol: str
    expiry: str
    strike: Decimal
    option_type: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    selection_score: float
    selection_reasons: list[str]


class RecommendedTradePlanResponse(BaseModel):
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


class AIRecommendationResponse(BaseModel):
    symbol: str
    action: str
    confidence: float
    risk: str
    entry: str
    stop_loss: str
    targets: list[str]
    position_size_pct: float
    summary: str
    pros: list[str]
    cons: list[str]
    reasoning: str
    selected_option: SelectedOptionResponse | None
    trade_plan: RecommendedTradePlanResponse | None


@router.get(
    "/recommendation/{symbol}",
    response_model=AIRecommendationResponse,
)
async def recommendation(
    symbol: str,
) -> AIRecommendationResponse:
    service = AIRecommendationService(get_broker())
    result = await service.recommend(symbol)

    selected_option = None

    if result.selected_option is not None:
        option = result.selected_option
        selected_option = SelectedOptionResponse(
            symbol=option.symbol,
            expiry=option.expiry,
            strike=option.strike,
            option_type=option.option_type,
            bid=option.bid,
            ask=option.ask,
            last=option.last,
            volume=option.volume,
            open_interest=option.open_interest,
            implied_volatility=option.implied_volatility,
            delta=option.delta,
            gamma=option.gamma,
            theta=option.theta,
            vega=option.vega,
            selection_score=option.selection_score,
            selection_reasons=list(option.selection_reasons),
        )

    trade_plan = None
    if result.trade_plan is not None:
        plan = result.trade_plan
        trade_plan = RecommendedTradePlanResponse(
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

    return AIRecommendationResponse(
        symbol=result.symbol,
        action=result.action,
        confidence=result.confidence,
        risk=result.risk,
        entry=result.entry,
        stop_loss=result.stop_loss,
        targets=list(result.targets),
        position_size_pct=result.position_size_pct,
        summary=result.summary,
        pros=list(result.pros),
        cons=list(result.cons),
        reasoning=result.reasoning,
        selected_option=selected_option,
        trade_plan=trade_plan,
    )
