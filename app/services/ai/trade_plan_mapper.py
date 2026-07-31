from __future__ import annotations

from app.services.ai.models import RecommendedTradePlan
from app.services.trade_risk.models import TradePlan


def to_recommended_trade_plan(trade_plan: TradePlan) -> RecommendedTradePlan:
    return RecommendedTradePlan(
        decision=trade_plan.decision,
        side=trade_plan.side,
        order_type=trade_plan.order_type,
        quantity=trade_plan.quantity,
        limit_price=trade_plan.limit_price,
        estimated_debit=trade_plan.estimated_debit,
        maximum_loss=trade_plan.maximum_loss,
        stop_price=trade_plan.stop_price,
        first_target_price=trade_plan.first_target_price,
        second_target_price=trade_plan.second_target_price,
        reward_risk_ratio=trade_plan.reward_risk_ratio,
        account_risk_pct=trade_plan.account_risk_pct,
        bid_ask_spread_pct=trade_plan.bid_ask_spread_pct,
        reasons=trade_plan.reasons,
        rejection_reasons=trade_plan.rejection_reasons,
    )
