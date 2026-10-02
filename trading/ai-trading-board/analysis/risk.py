"""Risk sub-score: higher score = lower risk (easier to blend with the other
sub-scores, where higher is always 'better')."""
from __future__ import annotations

import numpy as np
import pandas as pd


def analyze(prices: pd.DataFrame) -> dict:
    close = prices["Close"]
    returns = close.pct_change().dropna()
    notes: list[str] = []
    points = 0.0
    max_points = 0.0

    ann_vol = float(returns.std() * np.sqrt(252))
    max_points += 40
    if ann_vol < 0.20:
        points += 40
        notes.append(f"Annualized volatility {ann_vol*100:.1f}% — low")
    elif ann_vol < 0.35:
        points += 26
        notes.append(f"Annualized volatility {ann_vol*100:.1f}% — moderate")
    elif ann_vol < 0.55:
        points += 12
        notes.append(f"Annualized volatility {ann_vol*100:.1f}% — high")
    else:
        notes.append(f"Annualized volatility {ann_vol*100:.1f}% — extreme")

    running_max = close.cummax()
    drawdown = close / running_max - 1.0
    max_dd = float(drawdown.min())
    max_points += 40
    if max_dd > -0.15:
        points += 40
        notes.append(f"Max drawdown {max_dd*100:.1f}% (1y) — shallow")
    elif max_dd > -0.30:
        points += 26
        notes.append(f"Max drawdown {max_dd*100:.1f}% (1y) — moderate")
    elif max_dd > -0.50:
        points += 12
        notes.append(f"Max drawdown {max_dd*100:.1f}% (1y) — deep")
    else:
        notes.append(f"Max drawdown {max_dd*100:.1f}% (1y) — severe")

    downside = returns[returns < 0]
    max_points += 20
    if len(downside) > 5:
        skew = float(returns.skew())
        if skew >= 0:
            points += 20
            notes.append(f"Return skew {skew:.2f} — upside-biased tail risk")
        elif skew > -0.5:
            points += 12
            notes.append(f"Return skew {skew:.2f} — mild downside tail risk")
        else:
            points += 4
            notes.append(f"Return skew {skew:.2f} — sharp downside tail risk")
    else:
        points += 10

    score = round(100 * points / max_points, 1)
    return {
        "score": score,
        "annualized_volatility": round(ann_vol, 4),
        "max_drawdown": round(max_dd, 4),
        "notes": notes,
    }
