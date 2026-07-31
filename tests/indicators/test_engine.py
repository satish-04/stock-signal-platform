from datetime import datetime, timedelta, timezone

import pytest

from app.services.indicators.engine import IndicatorEngine
from app.services.indicators.models import Candle


def build_candles(
    closes: list[float],
    volume: float = 1_000.0,
) -> list[Candle]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    candles: list[Candle] = []

    for index, close in enumerate(closes):
        candles.append(
            Candle(
                timestamp=start + timedelta(minutes=5 * index),
                open=close - 0.5,
                high=close + 1.0,
                low=close - 1.0,
                close=close,
                volume=volume,
            )
        )

    return candles


def test_sma_returns_expected_value() -> None:
    result = IndicatorEngine.sma(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        period=3,
    )

    assert result == pytest.approx(4.0)


def test_ema_returns_value_after_minimum_period() -> None:
    result = IndicatorEngine.ema(
        [1.0, 2.0, 3.0, 4.0, 5.0],
        period=3,
    )

    assert result == pytest.approx(4.0)


def test_rsi_is_100_for_continuously_rising_prices() -> None:
    closes = [float(value) for value in range(1, 17)]

    result = IndicatorEngine.rsi(closes, period=14)

    assert result == pytest.approx(100.0)


def test_atr_returns_expected_value_for_constant_ranges() -> None:
    candles = build_candles(
        [100.0 + index for index in range(20)]
    )

    result = IndicatorEngine.atr(candles, period=14)

    assert result == pytest.approx(2.0)


def test_vwap_uses_typical_price_and_volume() -> None:
    candles = [
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=9.0,
            high=12.0,
            low=8.0,
            close=10.0,
            volume=100.0,
        ),
        Candle(
            timestamp=datetime.now(timezone.utc),
            open=19.0,
            high=22.0,
            low=18.0,
            close=20.0,
            volume=300.0,
        ),
    ]

    result = IndicatorEngine.vwap(candles)

    assert result == pytest.approx(17.5)


def test_bollinger_middle_matches_sma() -> None:
    values = [float(value) for value in range(1, 21)]

    upper, middle, lower = IndicatorEngine.bollinger_bands(
        values,
        period=20,
    )

    assert middle == pytest.approx(10.5)
    assert upper is not None
    assert lower is not None
    assert upper > middle > lower


def test_calculate_returns_all_available_indicators() -> None:
    closes = [
        100.0 + (index * 0.25)
        for index in range(220)
    ]
    candles = build_candles(closes)

    result = IndicatorEngine.calculate(candles)

    assert result.ema_9 is not None
    assert result.ema_20 is not None
    assert result.ema_50 is not None
    assert result.ema_200 is not None
    assert result.sma_20 is not None
    assert result.rsi_14 is not None
    assert result.macd is not None
    assert result.macd_signal is not None
    assert result.macd_histogram is not None
    assert result.atr_14 is not None
    assert result.vwap is not None
    assert result.bollinger_upper is not None
    assert result.bollinger_middle is not None
    assert result.bollinger_lower is not None


def test_calculate_rejects_empty_input() -> None:
    with pytest.raises(
        ValueError,
        match="At least one candle is required",
    ):
        IndicatorEngine.calculate([])


def test_calculate_rejects_invalid_high_low() -> None:
    candle = Candle(
        timestamp=datetime.now(timezone.utc),
        open=100.0,
        high=99.0,
        low=101.0,
        close=100.0,
        volume=1_000.0,
    )

    with pytest.raises(
        ValueError,
        match="high below low",
    ):
        IndicatorEngine.calculate([candle])


def test_calculate_rejects_negative_volume() -> None:
    candle = Candle(
        timestamp=datetime.now(timezone.utc),
        open=100.0,
        high=101.0,
        low=99.0,
        close=100.0,
        volume=-1.0,
    )

    with pytest.raises(
        ValueError,
        match="negative volume",
    ):
        IndicatorEngine.calculate([candle])
