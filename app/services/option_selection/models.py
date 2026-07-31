from __future__ import annotations

from dataclasses import dataclass

from app.services.options.models import OptionQuote


@dataclass(frozen=True)
class RankedOption:
    quote: OptionQuote
    score: float
    reasons: tuple[str, ...]
