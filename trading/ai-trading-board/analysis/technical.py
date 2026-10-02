"""Technical sub-score: trend, momentum, and volatility read from price history."""
from __future__ import annotations

import pandas as pd
import vectorbt as vbt


def analyze(prices: pd.DataFrame) -> dict:
    close = prices["Close"]
    notes: list[str] = []
    points = 0.0
    max_points = 0.0

    # --- Trend: price vs MA50 vs MA200 ---
    ma50 = vbt.MA.run(close, window=50, short_name="ma50").ma
    ma200 = vbt.MA.run(close, window=200, short_name="ma200").ma
    last_close = close.iloc[-1]
    last_ma50 = ma50.iloc[-1]
    last_ma200 = ma200.iloc[-1] if not pd.isna(ma200.iloc[-1]) else None

    max_points += 40
    if last_ma200 is not None:
        if last_close > last_ma50 > last_ma200:
            points += 40
            notes.append("Uptrend: price > MA50 > MA200")
        elif last_close < last_ma50 < last_ma200:
            notes.append("Downtrend: price < MA50 < MA200")
        elif last_close > last_ma200:
            points += 22
            notes.append("Above long-term trend (MA200) but choppy short-term")
        else:
            points += 8
            notes.append("Below long-term trend (MA200)")
    else:
        # not enough history for MA200 — fall back to MA50 only
        if last_close > last_ma50:
            points += 24
            notes.append("Above MA50 (insufficient history for MA200 read)")
        else:
            notes.append("Below MA50 (insufficient history for MA200 read)")

    # --- Momentum: RSI(14) ---
    rsi = vbt.RSI.run(close, window=14).rsi
    last_rsi = rsi.iloc[-1]
    max_points += 30
    if 45 <= last_rsi <= 65:
        points += 30
        notes.append(f"RSI {last_rsi:.1f} — healthy momentum")
    elif last_rsi < 30:
        points += 18
        notes.append(f"RSI {last_rsi:.1f} — oversold, possible bounce")
    elif last_rsi > 70:
        points += 10
        notes.append(f"RSI {last_rsi:.1f} — overbought, pullback risk")
    else:
        points += 20
        notes.append(f"RSI {last_rsi:.1f} — neutral")

    # --- Momentum confirmation: MACD ---
    macd_ind = vbt.MACD.run(close)
    macd_hist = (macd_ind.macd - macd_ind.signal).iloc[-1]
    max_points += 20
    if macd_hist > 0:
        points += 20
        notes.append("MACD above signal line — bullish momentum")
    else:
        notes.append("MACD below signal line — bearish momentum")

    # --- Volatility squeeze/expansion: Bollinger Band width trend ---
    bb = vbt.BBANDS.run(close, window=20)
    bb_width = ((bb.upper - bb.lower) / bb.middle).dropna()
    max_points += 10
    if len(bb_width) > 20:
        widening = bb_width.iloc[-1] > bb_width.iloc[-20:].mean()
        if widening:
            points += 10
            notes.append("Bollinger Band width expanding — volatility/trend picking up")
        else:
            points += 5
            notes.append("Bollinger Band width contracting — low volatility regime")
    else:
        points += 5

    score = round(100 * points / max_points, 1)
    return {
        "score": score,
        "last_close": round(float(last_close), 2),
        "rsi": round(float(last_rsi), 1),
        "ma50": round(float(last_ma50), 2),
        "ma200": round(float(last_ma200), 2) if last_ma200 is not None else None,
        "macd_hist": round(float(macd_hist), 4),
        "notes": notes,
    }
