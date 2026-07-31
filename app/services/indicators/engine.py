from __future__ import annotations

import math
from collections.abc import Sequence

from app.services.indicators.models import Candle, IndicatorResult


class IndicatorEngine:
    @staticmethod
    def _validate_candles(candles: Sequence[Candle]) -> None:
        if not candles:
            raise ValueError("At least one candle is required.")

        for index, candle in enumerate(candles):
            if candle.high < candle.low:
                raise ValueError(
                    f"Candle at index {index} has high below low."
                )

            if candle.volume < 0:
                raise ValueError(
                    f"Candle at index {index} has negative volume."
                )

    @staticmethod
    def sma(values: Sequence[float], period: int) -> float | None:
        if period <= 0:
            raise ValueError("SMA period must be greater than zero.")

        if len(values) < period:
            return None

        return sum(values[-period:]) / period

    @staticmethod
    def ema(values: Sequence[float], period: int) -> float | None:
        if period <= 0:
            raise ValueError("EMA period must be greater than zero.")

        if len(values) < period:
            return None

        seed = sum(values[:period]) / period
        multiplier = 2 / (period + 1)
        ema_value = seed

        for value in values[period:]:
            ema_value = (
                (value - ema_value) * multiplier
                + ema_value
            )

        return ema_value

    @staticmethod
    def _ema_series(
        values: Sequence[float],
        period: int,
    ) -> list[float | None]:
        if period <= 0:
            raise ValueError("EMA period must be greater than zero.")

        result: list[float | None] = [None] * len(values)

        if len(values) < period:
            return result

        seed = sum(values[:period]) / period
        result[period - 1] = seed

        multiplier = 2 / (period + 1)
        ema_value = seed

        for index in range(period, len(values)):
            ema_value = (
                (values[index] - ema_value) * multiplier
                + ema_value
            )
            result[index] = ema_value

        return result

    @staticmethod
    def rsi(values: Sequence[float], period: int = 14) -> float | None:
        if period <= 0:
            raise ValueError("RSI period must be greater than zero.")

        if len(values) < period + 1:
            return None

        gains: list[float] = []
        losses: list[float] = []

        for previous, current in zip(values, values[1:]):
            change = current - previous
            gains.append(max(change, 0.0))
            losses.append(max(-change, 0.0))

        average_gain = sum(gains[:period]) / period
        average_loss = sum(losses[:period]) / period

        for index in range(period, len(gains)):
            average_gain = (
                (average_gain * (period - 1)) + gains[index]
            ) / period
            average_loss = (
                (average_loss * (period - 1)) + losses[index]
            ) / period

        if average_loss == 0:
            return 100.0

        relative_strength = average_gain / average_loss
        return 100 - (100 / (1 + relative_strength))

    @staticmethod
    def macd(
        values: Sequence[float],
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
    ) -> tuple[float | None, float | None, float | None]:
        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("MACD periods must be greater than zero.")

        if fast_period >= slow_period:
            raise ValueError(
                "MACD fast period must be less than slow period."
            )

        fast_series = IndicatorEngine._ema_series(
            values,
            fast_period,
        )
        slow_series = IndicatorEngine._ema_series(
            values,
            slow_period,
        )

        macd_values: list[float] = []

        for fast_value, slow_value in zip(
            fast_series,
            slow_series,
        ):
            if fast_value is None or slow_value is None:
                continue

            macd_values.append(fast_value - slow_value)

        if not macd_values:
            return None, None, None

        macd_value = macd_values[-1]
        signal_value = IndicatorEngine.ema(
            macd_values,
            signal_period,
        )

        if signal_value is None:
            return macd_value, None, None

        histogram = macd_value - signal_value
        return macd_value, signal_value, histogram

    @staticmethod
    def atr(
        candles: Sequence[Candle],
        period: int = 14,
    ) -> float | None:
        if period <= 0:
            raise ValueError("ATR period must be greater than zero.")

        if len(candles) < period + 1:
            return None

        true_ranges: list[float] = []

        for previous, current in zip(candles, candles[1:]):
            true_range = max(
                current.high - current.low,
                abs(current.high - previous.close),
                abs(current.low - previous.close),
            )
            true_ranges.append(true_range)

        atr_value = sum(true_ranges[:period]) / period

        for true_range in true_ranges[period:]:
            atr_value = (
                (atr_value * (period - 1)) + true_range
            ) / period

        return atr_value

    @staticmethod
    def vwap(candles: Sequence[Candle]) -> float | None:
        total_volume = sum(candle.volume for candle in candles)

        if total_volume == 0:
            return None

        cumulative_price_volume = sum(
            (
                (candle.high + candle.low + candle.close) / 3
            )
            * candle.volume
            for candle in candles
        )

        return cumulative_price_volume / total_volume

    @staticmethod
    def bollinger_bands(
        values: Sequence[float],
        period: int = 20,
        standard_deviations: float = 2.0,
    ) -> tuple[float | None, float | None, float | None]:
        if period <= 0:
            raise ValueError(
                "Bollinger period must be greater than zero."
            )

        if standard_deviations <= 0:
            raise ValueError(
                "Bollinger standard deviations must be positive."
            )

        if len(values) < period:
            return None, None, None

        window = values[-period:]
        middle = sum(window) / period
        variance = sum(
            (value - middle) ** 2
            for value in window
        ) / period
        deviation = math.sqrt(variance)

        upper = middle + (standard_deviations * deviation)
        lower = middle - (standard_deviations * deviation)

        return upper, middle, lower

    @classmethod
    def calculate(
        cls,
        candles: Sequence[Candle],
    ) -> IndicatorResult:
        cls._validate_candles(candles)

        closes = [candle.close for candle in candles]

        macd_value, macd_signal, macd_histogram = cls.macd(
            closes
        )

        (
            bollinger_upper,
            bollinger_middle,
            bollinger_lower,
        ) = cls.bollinger_bands(closes)

        return IndicatorResult(
            ema_9=cls.ema(closes, 9),
            ema_20=cls.ema(closes, 20),
            ema_50=cls.ema(closes, 50),
            ema_200=cls.ema(closes, 200),
            sma_20=cls.sma(closes, 20),
            rsi_14=cls.rsi(closes, 14),
            macd=macd_value,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            atr_14=cls.atr(candles, 14),
            vwap=cls.vwap(candles),
            bollinger_upper=bollinger_upper,
            bollinger_middle=bollinger_middle,
            bollinger_lower=bollinger_lower,
        )
