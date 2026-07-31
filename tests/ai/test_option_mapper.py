from decimal import Decimal

from app.services.ai.option_mapper import to_selected_option
from app.services.option_selection.models import RankedOption
from app.services.options.models import OptionQuote


def test_to_selected_option_maps_ranked_quote() -> None:
    quote = OptionQuote(
        symbol="AAPL",
        expiry="2026-09-18",
        strike=Decimal(305),
        option_type="CALL",
        bid=Decimal("4.90"),
        ask=Decimal("5.10"),
        last=Decimal("5.00"),
        volume=1500,
        open_interest=6000,
        implied_volatility=0.32,
        delta=0.55,
        gamma=0.04,
        theta=-0.08,
        vega=0.12,
    )

    ranked = RankedOption(
        quote=quote,
        score=95.0,
        reasons=(
            "Delta is within the preferred directional range.",
            "Open interest is strong.",
        ),
    )

    result = to_selected_option(ranked)

    assert result.symbol == "AAPL"
    assert result.expiry == "2026-09-18"
    assert result.strike == Decimal(305)
    assert result.option_type == "CALL"
    assert result.bid == Decimal("4.90")
    assert result.ask == Decimal("5.10")
    assert result.last == Decimal("5.00")
    assert result.volume == 1500
    assert result.open_interest == 6000
    assert result.implied_volatility == 0.32
    assert result.delta == 0.55
    assert result.gamma == 0.04
    assert result.theta == -0.08
    assert result.vega == 0.12
    assert result.selection_score == 95.0
    assert result.selection_reasons == ranked.reasons
