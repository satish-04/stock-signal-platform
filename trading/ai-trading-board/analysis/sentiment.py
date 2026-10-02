"""Sentiment sub-score: cheap keyword heuristic over recent headlines.

Not NLP — just a lexicon scan. Good enough as a directional signal without
requiring any paid sentiment API or local model. Swap in FinBERT later if
the free-text signal proves useful.
"""
from __future__ import annotations

POSITIVE = {
    "beat", "beats", "surge", "surges", "soar", "soars", "rally", "rallies",
    "upgrade", "upgraded", "record", "growth", "outperform", "strong",
    "gain", "gains", "buy", "bullish", "raises", "raised", "profit",
    "expansion", "partnership", "breakthrough", "approval", "approved",
}
NEGATIVE = {
    "miss", "misses", "plunge", "plunges", "slump", "slumps", "downgrade",
    "downgraded", "layoff", "layoffs", "lawsuit", "investigation", "fraud",
    "recall", "decline", "declines", "weak", "loss", "losses", "sell",
    "bearish", "cuts", "cut", "warning", "delay", "delayed", "probe",
    "fine", "fined", "bankruptcy", "default",
}


def analyze(news: list[dict]) -> dict:
    if not news:
        return {"score": 50.0, "headline_count": 0, "notes": ["No recent headlines found — neutral default"]}

    pos = neg = 0
    for item in news:
        words = {w.strip(".,!?:;'\"").lower() for w in item["title"].split()}
        pos += len(words & POSITIVE)
        neg += len(words & NEGATIVE)

    total_hits = pos + neg
    if total_hits == 0:
        score = 50.0
        note = "Headlines carry no strong positive/negative language — neutral"
    else:
        # -1..+1 net polarity mapped onto 0..100
        polarity = (pos - neg) / total_hits
        score = round(50 + polarity * 50, 1)
        note = f"{pos} positive vs {neg} negative signal words across {len(news)} headlines"

    return {
        "score": score,
        "headline_count": len(news),
        "positive_hits": pos,
        "negative_hits": neg,
        "notes": [note],
        "sample_headlines": [n["title"] for n in news[:5]],
    }
