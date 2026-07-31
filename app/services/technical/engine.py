from dataclasses import asdict, dataclass
from typing import Any, Literal

Direction = Literal["bullish", "bearish", "neutral"]


@dataclass(frozen=True)
class TechnicalScore:
    score: float
    direction: Direction
    components: dict[str, float]
    evidence: dict[str, Any]
    warnings: list[str]

    def model_dump(self) -> dict[str, Any]:
        return asdict(self)


class TechnicalScoringEngine:
    """Deterministic, direction-aware technical scoring.

    Maximum score is 100 points:
      - EMA alignment: 25
      - VWAP position: 20
      - RSI confirmation: 20
      - Relative volume: 20
      - Multi-timeframe trend confirmation: 15

    Missing or contradictory evidence does not receive points. Unconfirmed bars
    are capped at 25 to prevent intrabar alerts from becoming actionable.
    """

    def score(self, technical: dict[str, Any], direction: Direction) -> TechnicalScore:
        indicators = technical.get("indicators") or {}
        warnings: list[str] = []
        components = {
            "ema_alignment": 0.0,
            "vwap_position": 0.0,
            "rsi_confirmation": 0.0,
            "relative_volume": 0.0,
            "multi_timeframe": 0.0,
        }

        if direction not in {"bullish", "bearish"}:
            return TechnicalScore(
                score=0.0,
                direction="neutral",
                components=components,
                evidence=indicators,
                warnings=["Neutral direction cannot receive a directional technical score"],
            )

        bullish = direction == "bullish"

        ema_fast = self._number(indicators.get("ema_fast"))
        ema_slow = self._number(indicators.get("ema_slow"))
        close = self._number(technical.get("close"))
        ema_aligned = indicators.get("ema_aligned")
        if isinstance(ema_aligned, bool):
            aligned = ema_aligned
        elif ema_fast is not None and ema_slow is not None and close is not None:
            aligned = close > ema_fast > ema_slow if bullish else close < ema_fast < ema_slow
        else:
            aligned = False
            warnings.append("EMA values/alignment missing")
        components["ema_alignment"] = 25.0 if aligned else 0.0

        above_vwap = indicators.get("above_vwap")
        if isinstance(above_vwap, bool):
            vwap_confirmed = above_vwap if bullish else not above_vwap
        else:
            vwap = self._number(indicators.get("vwap"))
            if vwap is None or close is None:
                vwap_confirmed = False
                warnings.append("VWAP position missing")
            else:
                vwap_confirmed = close > vwap if bullish else close < vwap
        components["vwap_position"] = 20.0 if vwap_confirmed else 0.0

        rsi = self._number(indicators.get("rsi"))
        if rsi is None:
            warnings.append("RSI missing")
        else:
            components["rsi_confirmation"] = self._rsi_points(rsi, bullish)

        relative_volume = self._number(indicators.get("relative_volume"))
        if relative_volume is None:
            warnings.append("Relative volume missing")
        else:
            components["relative_volume"] = self._relative_volume_points(relative_volume)

        mtf_fast = indicators.get("mtf_fast_trend")
        mtf_slow = indicators.get("mtf_slow_trend")
        expected = "bullish" if bullish else "bearish"
        if mtf_fast == expected:
            components["multi_timeframe"] += 7.5
        elif mtf_fast is None:
            warnings.append("Fast higher-timeframe trend missing")
        if mtf_slow == expected:
            components["multi_timeframe"] += 7.5
        elif mtf_slow is None:
            warnings.append("Slow higher-timeframe trend missing")

        total = round(sum(components.values()), 2)
        if not technical.get("bar_confirmed", False):
            total = min(total, 25.0)
            warnings.append("Unconfirmed bar score capped at 25")

        return TechnicalScore(
            score=total,
            direction=direction,
            components=components,
            evidence=indicators,
            warnings=warnings,
        )

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _rsi_points(rsi: float, bullish: bool) -> float:
        if bullish:
            if 55 <= rsi <= 70:
                return 20.0
            if 50 <= rsi < 55 or 70 < rsi <= 75:
                return 10.0
            return 0.0
        if 30 <= rsi <= 45:
            return 20.0
        if 25 <= rsi < 30 or 45 < rsi <= 50:
            return 10.0
        return 0.0

    @staticmethod
    def _relative_volume_points(relative_volume: float) -> float:
        if relative_volume >= 1.5:
            return 20.0
        if relative_volume >= 1.2:
            return 15.0
        if relative_volume >= 1.0:
            return 8.0
        return 0.0
