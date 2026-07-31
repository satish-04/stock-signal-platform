from dataclasses import dataclass
from app.core.config import get_settings

@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: list[str]

class RiskEngine:
    def __init__(self) -> None:
        self.settings = get_settings()

    def evaluate(self, candidate: dict, account_equity: float = 100000.0, open_positions: int = 0) -> RiskDecision:
        reasons: list[str] = []
        if candidate.get("strategy") == "no_trade": reasons.append("No valid strategy")
        max_loss = float(candidate.get("max_loss", 0))
        allowed = account_equity * self.settings.max_risk_per_trade_pct / 100
        if max_loss <= 0: reasons.append("Maximum loss is missing or non-positive")
        if max_loss > allowed: reasons.append(f"Maximum loss ${max_loss:.2f} exceeds ${allowed:.2f}")
        if open_positions >= self.settings.max_open_positions: reasons.append("Maximum open positions reached")
        return RiskDecision(approved=not reasons, reasons=reasons)
