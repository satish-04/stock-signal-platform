from __future__ import annotations

from app.services.indicators.models import IndicatorResult
from app.services.signals.models import TechnicalSignalResult


class TechnicalSignalEngine:
    @staticmethod
    def _clamp(value: float, minimum: float, maximum: float) -> float:
        return max(minimum, min(maximum, value))

    @classmethod
    def evaluate(
        cls,
        indicators: IndicatorResult,
        last_close: float,
        relative_volume: float | None = None,
    ) -> TechnicalSignalResult:
        reasons: list[str] = []
        warnings: list[str] = []

        bullish_points = 0.0
        bearish_points = 0.0

        trend_score = 0.0
        momentum_score = 0.0
        volatility_score = 0.0
        volume_score = 0.0

        ema_values = (
            indicators.ema_9,
            indicators.ema_20,
            indicators.ema_50,
            indicators.ema_200,
        )

        if all(value is not None for value in ema_values):
            ema_9 = float(indicators.ema_9)
            ema_20 = float(indicators.ema_20)
            ema_50 = float(indicators.ema_50)
            ema_200 = float(indicators.ema_200)

            if ema_9 > ema_20 > ema_50 > ema_200:
                bullish_points += 30.0
                trend_score = 30.0
                reasons.append("Bullish EMA alignment confirmed.")
            elif ema_9 < ema_20 < ema_50 < ema_200:
                bearish_points += 30.0
                trend_score = -30.0
                reasons.append("Bearish EMA alignment confirmed.")
            else:
                warnings.append("EMA alignment is mixed.")
        else:
            warnings.append("Insufficient EMA history.")

        if indicators.vwap is not None:
            if last_close > indicators.vwap:
                bullish_points += 10.0
                trend_score += 10.0
                reasons.append("Price is above VWAP.")
            elif last_close < indicators.vwap:
                bearish_points += 10.0
                trend_score -= 10.0
                reasons.append("Price is below VWAP.")
        else:
            warnings.append("VWAP is unavailable.")

        if indicators.rsi_14 is not None:
            rsi = indicators.rsi_14

            if 55.0 <= rsi <= 70.0:
                bullish_points += 15.0
                momentum_score += 15.0
                reasons.append("RSI confirms bullish momentum.")
            elif 30.0 <= rsi <= 45.0:
                bearish_points += 15.0
                momentum_score -= 15.0
                reasons.append("RSI confirms bearish momentum.")
            elif rsi > 70.0:
                warnings.append("RSI is overbought.")
            elif rsi < 30.0:
                warnings.append("RSI is oversold.")
            else:
                warnings.append("RSI is neutral.")
        else:
            warnings.append("RSI is unavailable.")

        if (
            indicators.macd is not None
            and indicators.macd_signal is not None
            and indicators.macd_histogram is not None
        ):
            if (
                indicators.macd > indicators.macd_signal
                and indicators.macd_histogram > 0
            ):
                bullish_points += 20.0
                momentum_score += 20.0
                reasons.append("MACD confirms bullish momentum.")
            elif (
                indicators.macd < indicators.macd_signal
                and indicators.macd_histogram < 0
            ):
                bearish_points += 20.0
                momentum_score -= 20.0
                reasons.append("MACD confirms bearish momentum.")
            else:
                warnings.append("MACD confirmation is mixed.")
        else:
            warnings.append("MACD is unavailable.")

        if indicators.atr_14 is not None and last_close > 0:
            atr_percent = (indicators.atr_14 / last_close) * 100.0

            if 0.5 <= atr_percent <= 3.0:
                bullish_points += 7.5
                bearish_points += 7.5
                volatility_score = 15.0
                reasons.append(
                    "ATR is within a tradable volatility range."
                )
            elif atr_percent > 5.0:
                volatility_score = -10.0
                warnings.append(
                    "ATR indicates elevated volatility risk."
                )
            else:
                volatility_score = 5.0
                warnings.append(
                    "ATR indicates limited price expansion."
                )
        else:
            warnings.append("ATR is unavailable.")

        if relative_volume is not None:
            if relative_volume >= 1.5:
                bullish_points += 5.0
                bearish_points += 5.0
                volume_score = 10.0
                reasons.append(
                    "Relative volume confirms participation."
                )
            elif relative_volume < 0.8:
                volume_score = -5.0
                warnings.append("Relative volume is weak.")
            else:
                volume_score = 5.0
                warnings.append("Relative volume is average.")
        else:
            warnings.append("Relative volume was not provided.")

        directional_edge = bullish_points - bearish_points

        if directional_edge >= 20.0:
            direction = "bullish"
        elif directional_edge <= -20.0:
            direction = "bearish"
        else:
            direction = "neutral"

        confidence = cls._clamp(
            abs(directional_edge)
            + max(volatility_score, 0.0)
            + max(volume_score, 0.0),
            0.0,
            100.0,
        )

        if direction == "neutral":
            confidence = min(confidence, 49.0)
            warnings.append(
                "Directional evidence is insufficient for a trade signal."
            )

        return TechnicalSignalResult(
            direction=direction,
            confidence=round(confidence, 2),
            trend_score=round(trend_score, 2),
            momentum_score=round(momentum_score, 2),
            volatility_score=round(volatility_score, 2),
            volume_score=round(volume_score, 2),
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )
