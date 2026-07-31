from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.brokers.factory import get_broker
from app.services.option_selection import OptionSelectionEngine, RankedOption
from app.services.options.service import OptionsService

router = APIRouter(
    prefix="/api/v1/options",
    tags=["options"],
)


class RankedOptionResponse(BaseModel):
    symbol: str
    expiry: str
    strike: Decimal
    option_type: str
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: int
    open_interest: int
    implied_volatility: float
    delta: float
    gamma: float
    theta: float
    vega: float
    score: float
    reasons: list[str]


class BestOptionsResponse(BaseModel):
    symbol: str
    generated_at: datetime
    best_call: RankedOptionResponse | None
    best_put: RankedOptionResponse | None


def _response_for(ranked: RankedOption | None) -> RankedOptionResponse | None:
    if ranked is None:
        return None

    quote = ranked.quote
    return RankedOptionResponse(
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
        score=ranked.score,
        reasons=list(ranked.reasons),
    )


@router.get("/best/{symbol}", response_model=BestOptionsResponse)
async def best_options(symbol: str) -> BestOptionsResponse:
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise HTTPException(status_code=422, detail="Symbol is required.")

    service = OptionsService(get_broker())

    try:
        quotes = await service.chain(normalized_symbol)
    except (NotImplementedError, PermissionError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Unable to load option chain for {normalized_symbol}.",
        ) from exc

    calls = OptionSelectionEngine.rank(quotes, option_type="CALL", limit=1)
    puts = OptionSelectionEngine.rank(quotes, option_type="PUT", limit=1)

    return BestOptionsResponse(
        symbol=normalized_symbol,
        generated_at=datetime.now(UTC),
        best_call=_response_for(calls[0] if calls else None),
        best_put=_response_for(puts[0] if puts else None),
    )
