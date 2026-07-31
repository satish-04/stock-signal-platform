from __future__ import annotations

from dataclasses import replace
from decimal import Decimal
from typing import Literal

from app.core.config import get_settings
from app.services.ai.factory import get_ai_client
from app.services.ai.models import (
    AIRecommendation,
    SelectedOptionContract,
    TradeAction,
)
from app.services.ai.option_mapper import to_selected_option
from app.services.ai.trade_plan_mapper import to_recommended_trade_plan
from app.services.brokers.base import BrokerAdapter
from app.services.indicators.service import IndicatorService
from app.services.option_selection.engine import OptionSelectionEngine
from app.services.options.service import OptionsService
from app.services.signals.models import SignalDirection
from app.services.signals.technical_engine import TechnicalSignalEngine
from app.services.trade_risk import (
    RiskLimits,
    TradeConstructionRequest,
    TradePlan,
    TradeRiskEngine,
)


class AIRecommendationService:
    def __init__(self, broker: BrokerAdapter) -> None:
        self.broker = broker
        self.indicators = IndicatorService(broker)
        self.options = OptionsService(broker)
        self.client = get_ai_client()
        self.settings = get_settings()

    @staticmethod
    def _option_type_for_direction(
        direction: SignalDirection,
    ) -> Literal["CALL", "PUT"] | None:
        if direction == "bullish":
            return "CALL"

        if direction == "bearish":
            return "PUT"

        return None

    @staticmethod
    def _action_for_direction(
        direction: SignalDirection,
    ) -> TradeAction:
        if direction == "bullish":
            return "BUY_CALL"

        if direction == "bearish":
            return "BUY_PUT"

        return "HOLD"

    async def _select_option(
        self,
        symbol: str,
        direction: SignalDirection,
    ) -> SelectedOptionContract | None:
        option_type = self._option_type_for_direction(direction)

        if option_type is None:
            return None

        quotes = await self.options.chain(symbol)
        ranked = OptionSelectionEngine.rank(
            quotes,
            option_type=option_type,
            limit=1,
        )

        if not ranked:
            return None

        return to_selected_option(ranked[0])

    @staticmethod
    def _selected_option_prompt(
        selected_option: SelectedOptionContract | None,
    ) -> str:
        if selected_option is None:
            return "No option contract was selected."

        return "\n".join(
            [
                "Selected option contract:",
                f"Symbol: {selected_option.symbol}",
                f"Type: {selected_option.option_type}",
                f"Expiry: {selected_option.expiry}",
                f"Strike: {selected_option.strike}",
                f"Bid: {selected_option.bid}",
                f"Ask: {selected_option.ask}",
                f"Last/Mid: {selected_option.last}",
                f"Delta: {selected_option.delta}",
                f"Gamma: {selected_option.gamma}",
                f"Theta: {selected_option.theta}",
                f"Vega: {selected_option.vega}",
                f"Implied volatility: {selected_option.implied_volatility}",
                f"Volume: {selected_option.volume}",
                f"Open interest: {selected_option.open_interest}",
                f"Selection score: {selected_option.selection_score}",
                "Selection reasons:",
                *selected_option.selection_reasons,
            ]
        )

    def _construct_trade_plan(
        self,
        symbol: str,
        action: TradeAction,
        confidence: float,
        selected_option: SelectedOptionContract | None,
    ) -> TradePlan | None:
        if selected_option is None or action == "HOLD":
            return None

        request = TradeConstructionRequest(
            symbol=symbol,
            option_symbol=(
                f"{selected_option.symbol} {selected_option.expiry} "
                f"{selected_option.option_type} {selected_option.strike}"
            ),
            option_type=selected_option.option_type,
            expiry=selected_option.expiry,
            strike=selected_option.strike,
            multiplier=100,
            bid=selected_option.bid,
            ask=selected_option.ask,
            last=selected_option.last,
            volume=selected_option.volume,
            open_interest=selected_option.open_interest,
            action=action,
            confidence=Decimal(str(confidence)),
            stop_loss_pct=Decimal(str(self.settings.option_stop_loss_pct)),
            first_target_pct=Decimal(str(self.settings.option_first_target_pct)),
            second_target_pct=Decimal(str(self.settings.option_second_target_pct)),
        )
        limits = RiskLimits(
            account_equity=Decimal(str(self.settings.risk_account_equity)),
            available_funds=Decimal(str(self.settings.risk_available_funds)),
            max_risk_per_trade_pct=Decimal(str(self.settings.max_risk_per_trade_pct)),
            max_position_value_pct=Decimal(str(self.settings.max_position_value_pct)),
            max_contracts=self.settings.max_option_contracts,
            max_bid_ask_spread_pct=Decimal(str(self.settings.max_option_spread_pct)),
            minimum_open_interest=self.settings.minimum_option_open_interest,
            minimum_volume=self.settings.minimum_option_volume,
            minimum_reward_risk_ratio=Decimal(
                str(self.settings.minimum_reward_risk_ratio)
            ),
        )
        return TradeRiskEngine.construct(request=request, limits=limits)

    async def recommend(
        self,
        symbol: str,
        duration: str = "5 D",
        bar_size: str = "5 mins",
        use_rth: bool = True,
    ) -> AIRecommendation:
        normalized_symbol = symbol.strip().upper()

        indicator_result = await self.indicators.calculate_for_symbol(
            symbol=normalized_symbol,
            duration=duration,
            bar_size=bar_size,
            use_rth=use_rth,
        )

        technical_signal = TechnicalSignalEngine.evaluate(
            indicators=indicator_result,
            last_close=float(indicator_result.ema_9 or 0),
            relative_volume=1.5,
        )

        selected_option = await self._select_option(
            symbol=normalized_symbol,
            direction=technical_signal.direction,
        )
        action = self._action_for_direction(technical_signal.direction)
        trade_plan = self._construct_trade_plan(
            symbol=normalized_symbol,
            action=action,
            confidence=technical_signal.confidence,
            selected_option=selected_option,
        )
        trade_plan_prompt = (
            "No trade plan was constructed."
            if trade_plan is None
            else "\n".join(
                [
                    "Deterministic trade-risk plan:",
                    f"Decision: {trade_plan.decision}",
                    f"Quantity: {trade_plan.quantity}",
                    f"Limit price: {trade_plan.limit_price}",
                    f"Maximum loss: {trade_plan.maximum_loss}",
                    f"Stop price: {trade_plan.stop_price}",
                    f"First target: {trade_plan.first_target_price}",
                    f"Second target: {trade_plan.second_target_price}",
                    f"Reward/risk ratio: {trade_plan.reward_risk_ratio}",
                    "Rejection reasons:",
                    *trade_plan.rejection_reasons,
                ]
            )
        )

        prompt = "\n".join(
            [
                f"Symbol: {normalized_symbol}",
                "",
                f"Direction: {technical_signal.direction}",
                f"Confidence: {technical_signal.confidence}",
                "",
                "Technical reasons:",
                *technical_signal.reasons,
                "",
                "Technical warnings:",
                *technical_signal.warnings,
                "",
                self._selected_option_prompt(selected_option),
                "",
                trade_plan_prompt,
                "",
                (
                    "Return a risk-aware recommendation that is consistent "
                    "with the technical direction and selected option contract."
                ),
            ]
        )

        recommendation = await self.client.recommend(prompt)

        return replace(
            recommendation,
            symbol=normalized_symbol,
            action=action,
            selected_option=selected_option,
            trade_plan=(
                to_recommended_trade_plan(trade_plan) if trade_plan is not None else None
            ),
        )
