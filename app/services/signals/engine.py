from dataclasses import dataclass
from typing import Literal

from app.core.config import get_settings

SignalStatus = Literal["rejected", "review", "actionable"]


@dataclass(frozen=True)
class SignalClassification:
    status: SignalStatus
    actionable: bool
    reason: str


class SignalEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    def score(
        self,
        news: dict,
        technical_score: float,
        options_quality: float = 80,
        regime: float = 70,
    ) -> tuple[float, dict[str, float]]:
        components = {
            "news": round(float(news.get("confidence", 0)) * 100, 2),
            "technical": round(float(technical_score), 2),
            "options_quality": round(float(options_quality), 2),
            "market_regime": round(float(regime), 2),
        }
        total = round(
            components["news"] * 0.35
            + components["technical"] * 0.30
            + components["options_quality"] * 0.25
            + components["market_regime"] * 0.10,
            2,
        )
        return total, components

    def classify(self, score: float, risk_approved: bool) -> SignalClassification:
        if not risk_approved:
            return SignalClassification(
                status="rejected",
                actionable=False,
                reason="Risk policy rejected the strategy candidate",
            )
        if score < self.settings.signal_review_threshold:
            return SignalClassification(
                status="rejected",
                actionable=False,
                reason=(
                    f"Score {score:.2f} is below review threshold "
                    f"{self.settings.signal_review_threshold:.2f}"
                ),
            )
        if score < self.settings.signal_actionable_threshold:
            return SignalClassification(
                status="review",
                actionable=False,
                reason=(
                    f"Score {score:.2f} requires human review; actionable threshold is "
                    f"{self.settings.signal_actionable_threshold:.2f}"
                ),
            )
        return SignalClassification(
            status="actionable",
            actionable=True,
            reason="Consensus and risk thresholds passed",
        )
