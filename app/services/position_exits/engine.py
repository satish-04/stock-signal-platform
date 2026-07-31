from datetime import UTC
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal

from app.services.position_exits.models import (
    ExitEvaluation,
    PositionExitContext,
    PositionExitRules,
)

ZERO = Decimal(0)
HUNDRED = Decimal(100)
TICK = Decimal("0.01")


class PositionExitEngine:
    @staticmethod
    def _round(value: Decimal) -> Decimal:
        return value.quantize(TICK, rounding=ROUND_HALF_UP)

    @staticmethod
    def _validate(rules: PositionExitRules, context: PositionExitContext) -> None:
        if not ZERO < rules.stop_loss_pct < HUNDRED:
            raise ValueError("stop_loss_pct must be between 0 and 100.")
        if rules.first_target_pct <= ZERO or rules.second_target_pct <= rules.first_target_pct:
            raise ValueError("Profit targets must be positive and ordered.")
        if not ZERO < rules.first_target_exit_pct <= HUNDRED:
            raise ValueError("first_target_exit_pct must be between 0 and 100.")
        if not ZERO < rules.trailing_distance_pct < HUNDRED:
            raise ValueError("trailing_distance_pct must be between 0 and 100.")
        if rules.max_holding_hours <= 0 or rules.stale_mark_seconds <= 0:
            raise ValueError("Time limits must be positive.")
        if (
            context.quantity <= 0
            or context.average_entry_price <= ZERO
            or context.current_mark_price <= ZERO
        ):
            raise ValueError("Position quantity and prices must be positive.")
        if any(
            value.tzinfo is None
            for value in (context.opened_at, context.evaluated_at, context.mark_updated_at)
        ):
            raise ValueError("Exit timestamps must be timezone-aware.")

    @classmethod
    def evaluate(cls, context: PositionExitContext, rules: PositionExitRules) -> ExitEvaluation:
        cls._validate(rules, context)
        evaluated = context.evaluated_at.astimezone(UTC)
        holding_hours = Decimal(
            str((evaluated - context.opened_at.astimezone(UTC)).total_seconds() / 3600)
        )
        mark_age = Decimal(
            str((evaluated - context.mark_updated_at.astimezone(UTC)).total_seconds())
        )
        return_pct = cls._round(
            (context.current_mark_price - context.average_entry_price)
            / context.average_entry_price
            * HUNDRED
        )
        days = None
        if context.expiration:
            days = cls._round(
                Decimal(
                    str((context.expiration.astimezone(UTC) - evaluated).total_seconds() / 86400)
                )
            )
        stop_price = cls._round(
            context.average_entry_price * (HUNDRED - rules.stop_loss_pct) / HUNDRED
        )
        first_price = cls._round(
            context.average_entry_price * (HUNDRED + rules.first_target_pct) / HUNDRED
        )
        second_price = cls._round(
            context.average_entry_price * (HUNDRED + rules.second_target_pct) / HUNDRED
        )
        trailing_price = cls._round(
            context.highest_mark_price * (HUNDRED - rules.trailing_distance_pct) / HUNDRED
        )
        reason = urgency = None
        trigger = None
        quantity = 0
        explanation = "No exit rule triggered."
        if mark_age > rules.stale_mark_seconds:
            reason, urgency, quantity = "STALE_MARK", "IMMEDIATE", context.quantity
            explanation = "Mark price is stale; close the paper position defensively."
        elif days is not None and days <= rules.expiration_exit_days:
            reason, urgency, quantity = "EXPIRATION_RISK", "IMMEDIATE", context.quantity
            explanation = "Position is inside the expiration-risk window."
        elif context.current_mark_price <= stop_price:
            reason, urgency, quantity, trigger = (
                "STOP_LOSS",
                "IMMEDIATE",
                context.quantity,
                stop_price,
            )
            explanation = "Hard stop-loss was reached."
        elif holding_hours >= rules.max_holding_hours:
            reason, urgency, quantity = "MAX_HOLDING_TIME", "HIGH", context.quantity
            explanation = "Maximum holding time was reached."
        elif context.current_mark_price >= second_price:
            reason, urgency, quantity, trigger = (
                "SECOND_TARGET",
                "HIGH",
                context.quantity,
                second_price,
            )
            explanation = "Second profit target was reached."
        elif (
            rules.trailing_stop_enabled
            and return_pct >= rules.trailing_activation_pct
            and context.current_mark_price <= trailing_price
        ):
            reason, urgency, quantity, trigger = (
                "TRAILING_STOP",
                "HIGH",
                context.quantity,
                trailing_price,
            )
            explanation = "Activated trailing stop was reached."
        elif not context.first_target_already_taken and context.current_mark_price >= first_price:
            raw = Decimal(context.quantity) * rules.first_target_exit_pct / HUNDRED
            quantity = max(1, int(raw.to_integral_value(rounding=ROUND_DOWN)))
            reason, urgency, trigger = "FIRST_TARGET", "NORMAL", first_price
            explanation = "First profit target was reached; take a partial exit."
        return ExitEvaluation(
            triggered=reason is not None,
            reason=reason,
            urgency=urgency,
            exit_quantity=quantity,
            mark_price=cls._round(context.current_mark_price),
            trigger_price=trigger,
            price_return_pct=return_pct,
            holding_hours=cls._round(holding_hours),
            days_to_expiration=days,
            mark_age_seconds=cls._round(mark_age),
            explanations=(explanation,),
            rejection_reasons=(),
        )
