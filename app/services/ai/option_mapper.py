from __future__ import annotations

from app.services.ai.models import SelectedOptionContract
from app.services.option_selection.models import RankedOption


def to_selected_option(
    ranked_option: RankedOption,
) -> SelectedOptionContract:
    quote = ranked_option.quote

    return SelectedOptionContract(
        symbol=quote.symbol,
        expiry=quote.expiry,
        strike=quote.strike,
        option_type=quote.option_type,
        bid=quote.bid,
        ask=quote.ask,
        last=quote.last,
        volume=quote.volume,
        open_interest=quote.open_interest,
        implied_volatility=quote.implied_volatility,
        delta=quote.delta,
        gamma=quote.gamma,
        theta=quote.theta,
        vega=quote.vega,
        selection_score=ranked_option.score,
        selection_reasons=ranked_option.reasons,
    )
