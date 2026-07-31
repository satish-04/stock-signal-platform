from app.services.technical.engine import TechnicalScoringEngine


def test_strong_bullish_setup_scores_100():
    result = TechnicalScoringEngine().score(
        {
            "close": 190,
            "bar_confirmed": True,
            "indicators": {
                "rsi": 61,
                "ema_fast": 188,
                "ema_slow": 184,
                "above_vwap": True,
                "relative_volume": 1.65,
                "mtf_fast_trend": "bullish",
                "mtf_slow_trend": "bullish",
            },
        },
        "bullish",
    )
    assert result.score == 100
    assert result.warnings == []


def test_strong_bearish_setup_scores_100():
    result = TechnicalScoringEngine().score(
        {
            "close": 180,
            "bar_confirmed": True,
            "indicators": {
                "rsi": 39,
                "ema_fast": 182,
                "ema_slow": 186,
                "above_vwap": False,
                "relative_volume": 1.55,
                "mtf_fast_trend": "bearish",
                "mtf_slow_trend": "bearish",
            },
        },
        "bearish",
    )
    assert result.score == 100


def test_missing_indicators_fail_closed():
    result = TechnicalScoringEngine().score(
        {"close": 100, "bar_confirmed": True, "indicators": {}},
        "bullish",
    )
    assert result.score == 0
    assert result.warnings


def test_unconfirmed_bar_is_capped():
    result = TechnicalScoringEngine().score(
        {
            "close": 190,
            "bar_confirmed": False,
            "indicators": {
                "rsi": 61,
                "ema_fast": 188,
                "ema_slow": 184,
                "above_vwap": True,
                "relative_volume": 1.65,
                "mtf_fast_trend": "bullish",
                "mtf_slow_trend": "bullish",
            },
        },
        "bullish",
    )
    assert result.score == 25
