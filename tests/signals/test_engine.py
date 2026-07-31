import pytest

from app.services.indicators.models import IndicatorResult
from app.services.signals.technical_engine import TechnicalSignalEngine


def build_indicators(
    *,
    ema_9: float = 110.0,
    ema_20: float = 108.0,
    ema_50: float = 105.0,
    ema_200: float = 100.0,
    rsi_14: float = 62.0,
    macd: float = 2.0,
    macd_signal: float = 1.0,
    macd_histogram: float = 1.0,
    atr_14: float = 2.0,
    vwap: float = 107.0,
) -> IndicatorResult:
    return IndicatorResult(
        ema_9=ema_9,
        ema_20=ema_20,
        ema_50=ema_50,
        ema_200=ema_200,
        sma_20=108.0,
        rsi_14=rsi_14,
        macd=macd,
        macd_signal=macd_signal,
        macd_histogram=macd_histogram,
        atr_14=atr_14,
        vwap=vwap,
        bollinger_upper=115.0,
        bollinger_middle=108.0,
        bollinger_lower=101.0,
    )


def test_bullish_signal() -> None:
    result = TechnicalSignalEngine.evaluate(
        indicators=build_indicators(),
        last_close=110.0,
        relative_volume=1.7,
    )

    assert result.direction == "bullish"
    assert result.confidence >= 80.0
    assert result.trend_score > 0
    assert result.momentum_score > 0
    assert "Bullish EMA alignment confirmed." in result.reasons
    assert "MACD confirms bullish momentum." in result.reasons


def test_bearish_signal() -> None:
    indicators = build_indicators(
        ema_9=90.0,
        ema_20=92.0,
        ema_50=95.0,
        ema_200=100.0,
        rsi_14=38.0,
        macd=-2.0,
        macd_signal=-1.0,
        macd_histogram=-1.0,
        vwap=93.0,
    )

    result = TechnicalSignalEngine.evaluate(
        indicators=indicators,
        last_close=90.0,
        relative_volume=1.6,
    )

    assert result.direction == "bearish"
    assert result.confidence >= 80.0
    assert result.trend_score < 0
    assert result.momentum_score < 0
    assert "Bearish EMA alignment confirmed." in result.reasons
    assert "MACD confirms bearish momentum." in result.reasons


def test_neutral_signal_when_directional_evidence_is_mixed() -> None:
    indicators = build_indicators(
        ema_9=101.0,
        ema_20=100.0,
        ema_50=102.0,
        ema_200=99.0,
        rsi_14=50.0,
        macd=1.0,
        macd_signal=1.0,
        macd_histogram=0.0,
        vwap=100.0,
    )

    result = TechnicalSignalEngine.evaluate(
        indicators=indicators,
        last_close=100.0,
        relative_volume=1.0,
    )

    assert result.direction == "neutral"
    assert result.confidence <= 49.0
    assert "Directional evidence is insufficient for a trade signal." in result.warnings


def test_overbought_rsi_adds_warning() -> None:
    result = TechnicalSignalEngine.evaluate(
        indicators=build_indicators(rsi_14=78.0),
        last_close=110.0,
        relative_volume=1.7,
    )

    assert "RSI is overbought." in result.warnings


def test_high_atr_adds_risk_warning() -> None:
    result = TechnicalSignalEngine.evaluate(
        indicators=build_indicators(atr_14=8.0),
        last_close=100.0,
        relative_volume=1.7,
    )

    assert result.volatility_score == -10.0
    assert "ATR indicates elevated volatility risk." in result.warnings


def test_missing_relative_volume_adds_warning() -> None:
    result = TechnicalSignalEngine.evaluate(
        indicators=build_indicators(),
        last_close=110.0,
    )

    assert result.volume_score == 0.0
    assert "Relative volume was not provided." in result.warnings


def test_confidence_is_capped_at_100() -> None:
    result = TechnicalSignalEngine.evaluate(
        indicators=build_indicators(),
        last_close=110.0,
        relative_volume=3.0,
    )

    assert result.confidence <= 100.0
