"""Unified market data access. yfinance today; swap in OpenBB/FMP later without
touching callers, since everything downstream just consumes plain DataFrames/dicts."""
from __future__ import annotations

import yfinance as yf
import pandas as pd


def fetch_prices(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No price data returned for {ticker!r} — check the ticker symbol.")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df


def fetch_fundamentals(ticker: str) -> dict:
    return yf.Ticker(ticker).info or {}


def fetch_news(ticker: str, limit: int = 15) -> list[dict]:
    try:
        items = yf.Ticker(ticker).news or []
    except Exception:
        return []
    out = []
    for item in items[:limit]:
        content = item.get("content", item)
        title = content.get("title") or item.get("title")
        if title:
            out.append({"title": title, "publisher": content.get("provider", {}).get("displayName", "")})
    return out
