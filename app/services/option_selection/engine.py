from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from app.services.option_selection.models import RankedOption
from app.services.options.models import OptionQuote


class OptionSelectionEngine:
    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> float:
        return max(minimum, min(maximum, value))

    @staticmethod
    def _mid_price(quote: OptionQuote) -> Decimal:
        return (quote.bid + quote.ask) / Decimal("2")

    @classmethod
    def score(
        cls,
        quote: OptionQuote,
    ) -> RankedOption:
        reasons: list[str] = []
        score = 0.0

        absolute_delta = abs(quote.delta)

        # Delta quality: maximum 30 points.
        if 0.45 <= absolute_delta <= 0.65:
            score += 30.0
            reasons.append(
                "Delta is within the preferred directional range."
            )
        elif 0.30 <= absolute_delta < 0.45:
            score += 20.0
            reasons.append(
                "Delta provides moderate directional exposure."
            )
        elif 0.65 < absolute_delta <= 0.80:
            score += 18.0
            reasons.append(
                "Delta provides stronger intrinsic exposure."
            )
        else:
            reasons.append(
                "Delta is outside the preferred range."
            )

        # Liquidity: maximum 30 points.
        if quote.open_interest >= 5_000:
            score += 15.0
            reasons.append("Open interest is strong.")
        elif quote.open_interest >= 1_000:
            score += 10.0
            reasons.append("Open interest is acceptable.")
        else:
            reasons.append("Open interest is limited.")

        if quote.volume >= 1_000:
            score += 15.0
            reasons.append("Trading volume is strong.")
        elif quote.volume >= 250:
            score += 10.0
            reasons.append("Trading volume is acceptable.")
        else:
            reasons.append("Trading volume is limited.")

        # Bid/ask spread: maximum 20 points.
        mid_price = cls._mid_price(quote)
        spread = quote.ask - quote.bid

        if mid_price > 0:
            spread_percent = float(spread / mid_price) * 100.0

            if spread_percent <= 5.0:
                score += 20.0
                reasons.append("Bid/ask spread is tight.")
            elif spread_percent <= 10.0:
                score += 12.0
                reasons.append("Bid/ask spread is acceptable.")
            elif spread_percent <= 20.0:
                score += 5.0
                reasons.append("Bid/ask spread is relatively wide.")
            else:
                reasons.append("Bid/ask spread is too wide.")
        else:
            reasons.append("Option midpoint is unavailable.")

        # Implied volatility: maximum 15 points.
        if 0.20 <= quote.implied_volatility <= 0.45:
            score += 15.0
            reasons.append(
                "Implied volatility is within a preferred range."
            )
        elif 0.10 <= quote.implied_volatility < 0.20:
            score += 10.0
            reasons.append("Implied volatility is relatively low.")
        elif 0.45 < quote.implied_volatility <= 0.70:
            score += 7.0
            reasons.append("Implied volatility is elevated.")
        else:
            reasons.append(
                "Implied volatility is outside the preferred range."
            )

        # Greek stability: maximum 5 points.
        if quote.gamma <= 0.10 and abs(quote.theta) <= 0.15:
            score += 5.0
            reasons.append(
                "Gamma and theta are within acceptable limits."
            )
        else:
            reasons.append(
                "Gamma or theta indicates elevated contract risk."
            )

        return RankedOption(
            quote=quote,
            score=round(cls._clamp(score), 2),
            reasons=tuple(reasons),
        )

    @classmethod
    def rank(
        cls,
        quotes: Iterable[OptionQuote],
        option_type: str | None = None,
        limit: int | None = None,
    ) -> list[RankedOption]:
        normalized_type = (
            option_type.upper()
            if option_type is not None
            else None
        )

        if normalized_type not in {None, "CALL", "PUT"}:
            raise ValueError(
                "option_type must be CALL, PUT, or None."
            )

        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be greater than zero."
            )

        filtered_quotes = [
            quote
            for quote in quotes
            if (
                normalized_type is None
                or quote.option_type == normalized_type
            )
        ]

        ranked = sorted(
            (
                cls.score(quote)
                for quote in filtered_quotes
            ),
            key=lambda item: (
                item.score,
                item.quote.open_interest,
                item.quote.volume,
            ),
            reverse=True,
        )

        if limit is not None:
            return ranked[:limit]

        return ranked
