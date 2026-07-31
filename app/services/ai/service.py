from __future__ import annotations

from dataclasses import replace
from typing import Literal

from app.services.ai.factory import get_ai_client
from app.services.ai.models import (
    AIRecommendation,
    SelectedOptionContract,
    TradeAction,
)
from app.services.ai.option_mapper import to_selected_option
from app.services.brokers.base import BrokerAdapter
from app.services.indicators.service import IndicatorService
from app.services.option_selection.engine import OptionSelectionEngine
from app.services.options.service import OptionsService
from app.services.signals.models import SignalDirection
from app.services.signals.technical_engine import TechnicalSignalEngine


class AIRecommendationService:
    def __init__(self, broker: BrokerAdapter) -> None:
        self.broker = broker
        self.indicators = IndicatorService(broker)
        self.options = OptionsService(broker)
        self.client = get_ai_client()

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
            action=self._action_for_direction(technical_signal.direction),
            selected_option=selected_option,
        )
