"""Fundamental sub-score: valuation, growth, profitability, balance sheet health.

Pulled from yfinance's `.info` dict, which is best-effort (fields vary by
ticker/exchange) so every lookup is defensive.
"""
from __future__ import annotations


def _get(info: dict, *keys, default=None):
    for k in keys:
        v = info.get(k)
        if v is not None:
            return v
    return default


def analyze(info: dict) -> dict:
    notes: list[str] = []
    points = 0.0
    max_points = 0.0

    pe = _get(info, "trailingPE", "forwardPE")
    max_points += 25
    if pe is None:
        notes.append("P/E unavailable")
    elif pe <= 0:
        notes.append(f"Negative/undefined P/E ({pe:.1f}) — unprofitable or distorted earnings")
    elif pe < 15:
        points += 25
        notes.append(f"P/E {pe:.1f} — cheap relative to typical market multiple")
    elif pe < 30:
        points += 16
        notes.append(f"P/E {pe:.1f} — reasonable valuation")
    else:
        points += 6
        notes.append(f"P/E {pe:.1f} — expensive, priced for high growth")

    growth = _get(info, "revenueGrowth")
    max_points += 25
    if growth is None:
        notes.append("Revenue growth unavailable")
    elif growth > 0.20:
        points += 25
        notes.append(f"Revenue growth {growth*100:.1f}% — strong")
    elif growth > 0.05:
        points += 17
        notes.append(f"Revenue growth {growth*100:.1f}% — moderate")
    elif growth > 0:
        points += 9
        notes.append(f"Revenue growth {growth*100:.1f}% — slow")
    else:
        notes.append(f"Revenue growth {growth*100:.1f}% — shrinking")

    margin = _get(info, "profitMargins")
    max_points += 25
    if margin is None:
        notes.append("Profit margin unavailable")
    elif margin > 0.15:
        points += 25
        notes.append(f"Net margin {margin*100:.1f}% — highly profitable")
    elif margin > 0.05:
        points += 16
        notes.append(f"Net margin {margin*100:.1f}% — profitable")
    elif margin > 0:
        points += 8
        notes.append(f"Net margin {margin*100:.1f}% — thin margins")
    else:
        notes.append(f"Net margin {margin*100:.1f}% — unprofitable")

    de = _get(info, "debtToEquity")
    max_points += 25
    if de is None:
        notes.append("Debt/Equity unavailable")
    elif de < 50:
        points += 25
        notes.append(f"Debt/Equity {de:.0f} — low leverage")
    elif de < 100:
        points += 17
        notes.append(f"Debt/Equity {de:.0f} — moderate leverage")
    elif de < 200:
        points += 9
        notes.append(f"Debt/Equity {de:.0f} — high leverage")
    else:
        notes.append(f"Debt/Equity {de:.0f} — very high leverage")

    score = round(100 * points / max_points, 1) if max_points else None
    return {
        "score": score,
        "pe": pe,
        "revenue_growth": growth,
        "profit_margin": margin,
        "debt_to_equity": de,
        "market_cap": _get(info, "marketCap"),
        "sector": _get(info, "sector"),
        "notes": notes,
    }
