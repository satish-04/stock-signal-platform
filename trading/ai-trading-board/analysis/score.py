"""Composite Trade Score: weighted blend of technical/fundamental/sentiment/risk.

Weights mirror the industry pattern documented in the vault's
`zubair-trabzada-ai-trading-hermes.md` notes (technical/fundamental as the
two largest factors, sentiment and risk as modifiers) collapsed from 5
categories to 4 since we don't run a separate LLM "thesis" agent here.
"""
from __future__ import annotations

from . import technical, fundamental, sentiment, risk
from data.provider import fetch_prices, fetch_fundamentals, fetch_news

WEIGHTS = {"technical": 0.30, "fundamental": 0.30, "sentiment": 0.20, "risk": 0.20}


def _grade(score: float) -> str:
    if score >= 80:
        return "Strong Buy"
    if score >= 60:
        return "Buy"
    if score >= 40:
        return "Hold"
    if score >= 20:
        return "Caution"
    return "Avoid"


def analyze_ticker(ticker: str) -> dict:
    ticker = ticker.upper()
    prices = fetch_prices(ticker, period="1y", interval="1d")
    info = fetch_fundamentals(ticker)
    news = fetch_news(ticker)

    tech = technical.analyze(prices)
    fund = fundamental.analyze(info)
    sent = sentiment.analyze(news)
    rsk = risk.analyze(prices)

    parts = {"technical": tech["score"], "fundamental": fund["score"], "sentiment": sent["score"], "risk": rsk["score"]}

    # If fundamentals are unavailable (e.g. some crypto/ETF tickers), redistribute
    # its weight across the remaining components instead of silently zeroing it.
    available = {k: v for k, v in parts.items() if v is not None}
    weight_sum = sum(WEIGHTS[k] for k in available)
    composite = sum(parts[k] * WEIGHTS[k] for k in available) / weight_sum
    composite = round(composite, 1)

    return {
        "ticker": ticker,
        "composite_score": composite,
        "grade": _grade(composite),
        "sub_scores": parts,
        "weights": WEIGHTS,
        "technical": tech,
        "fundamental": fund,
        "sentiment": sent,
        "risk": rsk,
        "company_name": info.get("longName") or info.get("shortName") or ticker,
    }
