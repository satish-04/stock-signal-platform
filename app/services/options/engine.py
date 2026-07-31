from decimal import Decimal
from app.services.brokers.base import OptionContractSnapshot

class OptionsEngine:
    @staticmethod
    def liquid(c: OptionContractSnapshot) -> bool:
        mid = (c.bid + c.ask) / 2
        spread_pct = float((c.ask - c.bid) / mid * 100) if mid else 999.0
        return c.volume >= 100 and c.open_interest >= 500 and spread_pct <= 10

    def choose_defined_risk(self, direction: str, chain: list[OptionContractSnapshot]) -> dict:
        liquid = [c for c in chain if self.liquid(c)]
        if direction == "bullish":
            calls = sorted([c for c in liquid if c.right == "C"], key=lambda c: c.strike)
            if len(calls) >= 2:
                long, short = calls[0], calls[1]
                debit = long.ask - short.bid
                width = short.strike - long.strike
                return {"strategy": "call_debit_spread", "long_conid": long.conid, "short_conid": short.conid,
                        "max_debit": float(debit), "max_loss": float(debit * 100),
                        "max_profit": float((width - debit) * 100)}
        if direction == "bearish":
            puts = sorted([c for c in liquid if c.right == "P"], key=lambda c: c.strike, reverse=True)
            if len(puts) >= 2:
                long, short = puts[0], puts[1]
                debit = long.ask - short.bid
                width = long.strike - short.strike
                return {"strategy": "put_debit_spread", "long_conid": long.conid, "short_conid": short.conid,
                        "max_debit": float(debit), "max_loss": float(debit * 100),
                        "max_profit": float((width - debit) * 100)}
        return {"strategy": "no_trade", "reason": "No liquid defined-risk structure"}
