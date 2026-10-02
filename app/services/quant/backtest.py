"""Deterministic daily-bar backtests with parameter sweeps and walk-forward validation.

Every position is decided from data up to and including the close of day t and earns the
return of day t+1, so no result here can see the future. A parameter set chosen on the
full sample is still fitted to that sample; the walk-forward result, which only ever
trades parameters chosen on earlier data, is the honest estimate.
"""
import math
from dataclasses import dataclass
from itertools import product, pairwise
from typing import Any

TRADING_DAYS = 252

GRIDS: dict[str, dict[str, list[int]]] = {
    "ema_cross": {"fast": [5, 10, 20, 30], "slow": [50, 100, 150, 200]},
    "rsi_reversion": {"period": [7, 14, 21], "entry": [25, 30, 35], "exit": [50, 60, 70]},
}


@dataclass(frozen=True)
class PriceHistory:
    symbol: str
    dates: list[str]
    closes: list[float]


def ema(values: list[float], period: int) -> list[float]:
    alpha = 2 / (period + 1)
    out = [values[0]]
    for value in values[1:]:
        out.append(out[-1] + alpha * (value - out[-1]))
    return out


def rsi(values: list[float], period: int) -> list[float | None]:
    """Wilder's RSI. None until ``period`` changes have been seen."""
    out: list[float | None] = [None] * len(values)
    if len(values) <= period:
        return out
    changes = [b - a for a, b in pairwise(values)]
    gain = sum(max(c, 0.0) for c in changes[:period]) / period
    loss = sum(max(-c, 0.0) for c in changes[:period]) / period
    for index in range(period, len(values)):
        if index > period:
            change = changes[index - 1]
            gain = (gain * (period - 1) + max(change, 0.0)) / period
            loss = (loss * (period - 1) + max(-change, 0.0)) / period
        out[index] = 100.0 if loss == 0 else 100 - 100 / (1 + gain / loss)
    return out


def positions(strategy: str, closes: list[float], params: dict[str, int]) -> list[int]:
    """Long (1) or flat (0) at each close, using only prices up to that close."""
    if strategy == "ema_cross":
        fast, slow = ema(closes, params["fast"]), ema(closes, params["slow"])
        warmup = params["slow"]
        return [1 if i >= warmup and fast[i] > slow[i] else 0 for i in range(len(closes))]
    if strategy == "rsi_reversion":
        values = rsi(closes, params["period"])
        out, held = [], 0
        for value in values:
            if value is not None:
                if not held and value < params["entry"]:
                    held = 1
                elif held and value > params["exit"]:
                    held = 0
            out.append(held)
        return out
    raise ValueError(f"Unknown strategy: {strategy}")


def strategy_returns(closes: list[float], held: list[int], cost_bps: float) -> list[float]:
    """Daily strategy returns; index i is the return earned on day i+1."""
    cost = cost_bps / 10_000
    out = []
    for i in range(len(closes) - 1):
        change = abs(held[i] - (held[i - 1] if i else 0))
        out.append(held[i] * (closes[i + 1] / closes[i] - 1) - change * cost)
    return out


def metrics(returns: list[float], held: list[int] | None = None) -> dict[str, Any]:
    if not returns:
        return {"total_return_pct": 0.0, "cagr_pct": 0.0, "volatility_pct": 0.0, "sharpe": 0.0,
                "max_drawdown_pct": 0.0, "trades": 0, "win_rate_pct": None, "exposure_pct": 0.0}
    equity, peak, drawdown = 1.0, 1.0, 0.0
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        drawdown = min(drawdown, equity / peak - 1)
    mean = sum(returns) / len(returns)
    variance = sum((value - mean) ** 2 for value in returns) / max(len(returns) - 1, 1)
    deviation = math.sqrt(variance)
    years = len(returns) / TRADING_DAYS
    trades, wins = _trades(returns, held) if held is not None else (0, 0)
    return {
        "total_return_pct": round((equity - 1) * 100, 2),
        "cagr_pct": round((equity ** (1 / years) - 1) * 100, 2) if equity > 0 else -100.0,
        "volatility_pct": round(deviation * math.sqrt(TRADING_DAYS) * 100, 2),
        "sharpe": round(mean / deviation * math.sqrt(TRADING_DAYS), 2) if deviation > 0 else 0.0,
        "max_drawdown_pct": round(drawdown * 100, 2),
        "trades": trades,
        "win_rate_pct": round(wins / trades * 100, 1) if trades else None,
        "exposure_pct": round(sum(held[: len(returns)]) / len(returns) * 100, 1) if held else 0.0,
    }


def _trades(returns: list[float], held: list[int]) -> tuple[int, int]:
    trades = wins = 0
    growth, open_trade = 1.0, False
    for i, value in enumerate(returns):
        if held[i]:
            growth, open_trade = growth * (1 + value) if open_trade else 1 + value, True
        if open_trade and (not held[i] or i == len(returns) - 1):
            trades += 1
            wins += growth > 1
            open_trade = False
    return trades, wins


def _combinations(strategy: str) -> list[dict[str, int]]:
    grid = GRIDS[strategy]
    combos = [dict(zip(grid, values, strict=True)) for values in product(*grid.values())]
    if strategy == "ema_cross":
        combos = [combo for combo in combos if combo["fast"] < combo["slow"]]
    return combos


def run_backtest(
    history: PriceHistory,
    strategy: str,
    cost_bps: float = 5.0,
    train_days: int = 2 * TRADING_DAYS,
    test_days: int = TRADING_DAYS // 2,
) -> dict[str, Any]:
    closes = history.closes
    runs = []
    for params in _combinations(strategy):
        held = positions(strategy, closes, params)
        returns = strategy_returns(closes, held, cost_bps)
        runs.append({"params": params, "held": held, "returns": returns, **metrics(returns, held)})
    runs.sort(key=lambda run: run["sharpe"], reverse=True)
    best = runs[0]
    hold = [1] * len(closes)
    benchmark = strategy_returns(closes, hold, 0.0)

    public = lambda run: {k: v for k, v in run.items() if k not in ("held", "returns")}
    return {
        "symbol": history.symbol,
        "strategy": strategy,
        "bars": len(closes),
        "start": history.dates[0],
        "end": history.dates[-1],
        "cost_bps": cost_bps,
        "combinations": len(runs),
        "best": public(best),
        "top": [public(run) for run in runs[:10]],
        "benchmark": metrics(benchmark, hold),
        "equity_curve": _curve(history.dates, best["returns"], benchmark),
        "walk_forward": _walk_forward(history.dates, runs, train_days, test_days),
    }


def _walk_forward(
    dates: list[str], runs: list[dict[str, Any]], train_days: int, test_days: int
) -> dict[str, Any] | None:
    """Pick the best parameters on each training window, then trade them on the next one."""
    total = len(runs[0]["returns"])
    if total < train_days + test_days:
        return None
    sharpe = lambda values: metrics(values)["sharpe"]
    windows, stitched, held = [], [], []
    start = 0
    while start + train_days + test_days <= total:
        split, end = start + train_days, start + train_days + test_days
        chosen = max(runs, key=lambda run: sharpe(run["returns"][start:split]))
        out_of_sample = chosen["returns"][split:end]
        stitched += out_of_sample
        held += chosen["held"][split:end]
        windows.append({
            "train_start": dates[start], "test_start": dates[split], "test_end": dates[end],
            "params": chosen["params"],
            "in_sample_sharpe": sharpe(chosen["returns"][start:split]),
            "out_of_sample_sharpe": sharpe(out_of_sample),
        })
        start += test_days
    in_sample = sum(window["in_sample_sharpe"] for window in windows) / len(windows)
    result = metrics(stitched, held)
    return {
        "train_days": train_days,
        "test_days": test_days,
        "windows": windows,
        "out_of_sample": result,
        "average_in_sample_sharpe": round(in_sample, 2),
        # How much of the in-sample edge survives on unseen data. Near zero or negative means
        # the sweep is fitting noise.
        "sharpe_retained_pct": round(result["sharpe"] / in_sample * 100, 1) if in_sample > 0 else None,
    }


def _curve(dates: list[str], strategy: list[float], benchmark: list[float], points: int = 250) -> list[dict]:
    step = max(len(strategy) // points, 1)
    curve, a, b = [], 1.0, 1.0
    for i, (x, y) in enumerate(zip(strategy, benchmark, strict=True)):
        a, b = a * (1 + x), b * (1 + y)
        if i % step == 0 or i == len(strategy) - 1:
            curve.append({"date": dates[i + 1], "strategy": round(a, 4), "benchmark": round(b, 4)})
    return curve
