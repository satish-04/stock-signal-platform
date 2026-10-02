"""Strategy research via VectorBT — the "10,000 combos in seconds" superpower
called out in the vault's plan docs. Two baseline strategies: MA crossover
(trend-following) and RSI mean-reversion. Each has a single-run mode and a
param-sweep mode.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import vectorbt as vbt

FEES = 0.001
SLIPPAGE = 0.0005


def _stats_dict(pf: "vbt.Portfolio") -> dict:
    return {
        "total_return_pct": round(float(pf.total_return()) * 100, 2),
        "sharpe_ratio": round(float(pf.sharpe_ratio()), 2),
        "max_drawdown_pct": round(float(pf.max_drawdown()) * 100, 2),
        "win_rate_pct": round(float(pf.trades.win_rate()) * 100, 2) if pf.trades.count() > 0 else None,
        "num_trades": int(pf.trades.count()),
    }


def run_ma_crossover(prices: pd.DataFrame, fast_window: int = 10, slow_window: int = 50) -> dict:
    close = prices["Close"]
    fast_ma = vbt.MA.run(close, window=fast_window, short_name="fast")
    slow_ma = vbt.MA.run(close, window=slow_window, short_name="slow")
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.Portfolio.from_signals(close, entries, exits, fees=FEES, slippage=SLIPPAGE, freq="1D")
    return {"strategy": "ma_crossover", "params": {"fast_window": fast_window, "slow_window": slow_window}, **_stats_dict(pf)}


def sweep_ma_crossover(prices: pd.DataFrame, windows=range(5, 55, 5), top_n: int = 5) -> list[dict]:
    close = prices["Close"]
    fast_ma, slow_ma = vbt.MA.run_combs(close, window=list(windows), r=2, short_names=["fast", "slow"])
    entries = fast_ma.ma_crossed_above(slow_ma)
    exits = fast_ma.ma_crossed_below(slow_ma)
    pf = vbt.Portfolio.from_signals(close, entries, exits, fees=FEES, slippage=SLIPPAGE, freq="1D")

    sharpe = pf.sharpe_ratio()
    ranked = sharpe.sort_values(ascending=False).dropna()
    results = []
    for combo in ranked.index[:top_n]:
        fast_w, slow_w = combo[0], combo[1]
        single = pf[combo]
        results.append({
            "params": {"fast_window": int(fast_w), "slow_window": int(slow_w)},
            **_stats_dict_from_single(single),
        })
    return results


def _stats_dict_from_single(pf_col) -> dict:
    return {
        "total_return_pct": round(float(pf_col.total_return()) * 100, 2),
        "sharpe_ratio": round(float(pf_col.sharpe_ratio()), 2),
        "max_drawdown_pct": round(float(pf_col.max_drawdown()) * 100, 2),
        "num_trades": int(pf_col.trades.count()),
    }


def run_rsi_reversion(prices: pd.DataFrame, window: int = 14, lower: int = 30, upper: int = 70) -> dict:
    close = prices["Close"]
    rsi = vbt.RSI.run(close, window=window).rsi
    entries = rsi < lower
    exits = rsi > upper
    pf = vbt.Portfolio.from_signals(close, entries, exits, fees=FEES, slippage=SLIPPAGE, freq="1D")
    return {"strategy": "rsi_reversion", "params": {"window": window, "lower": lower, "upper": upper}, **_stats_dict(pf)}


def sweep_rsi_reversion(
    prices: pd.DataFrame,
    windows=(10, 14, 21),
    lowers=(20, 25, 30),
    uppers=(70, 75, 80),
    top_n: int = 5,
) -> list[dict]:
    close = prices["Close"]
    results = []
    for w in windows:
        rsi = vbt.RSI.run(close, window=w).rsi
        for lo in lowers:
            for hi in uppers:
                entries = rsi < lo
                exits = rsi > hi
                pf = vbt.Portfolio.from_signals(close, entries, exits, fees=FEES, slippage=SLIPPAGE, freq="1D")
                if pf.trades.count() == 0:
                    continue
                results.append({"params": {"window": w, "lower": lo, "upper": hi}, **_stats_dict(pf)})
    results.sort(key=lambda r: (r["sharpe_ratio"] if not np.isnan(r["sharpe_ratio"]) else -999), reverse=True)
    return results[:top_n]
