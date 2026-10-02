import re
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

from app.services.quant import service

router = APIRouter(prefix="/api/v1/quant", tags=["quant"])

SYMBOL_PATTERN = re.compile(r"[A-Z0-9^][A-Z0-9.\-]{0,15}")


def _symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise ValueError("Invalid symbol")
    return symbol


class BacktestRequest(BaseModel):
    symbol: str
    strategy: Literal["ema_cross", "rsi_reversion"] = "ema_cross"
    years: int = Field(default=5, ge=2, le=15)
    cost_bps: float = Field(default=5.0, ge=0, le=100)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return _symbol(value)


@router.post("/backtest")
async def run_backtest(request: BacktestRequest) -> dict:
    """Sweep a strategy's parameters on daily history and validate them walk-forward."""
    try:
        result = await service.backtest(request.symbol, request.strategy, request.years, request.cost_bps)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Price history unavailable: {exc}"[:200]) from exc
    if result is None:
        raise HTTPException(status_code=404, detail=f"Not enough price history for {request.symbol}")
    return result


@router.get("/regime")
async def market_regime(symbol: str = Query(default="SPY", min_length=1, max_length=16)) -> dict:
    try:
        result = await service.market_regime(_symbol(symbol))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Price history unavailable: {exc}"[:200]) from exc
    if result is None:
        raise HTTPException(status_code=404, detail=f"Not enough price history for {symbol}")
    return result
