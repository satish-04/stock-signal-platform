"""Simulated paper-trading ledger — a local JSON file standing in for
Freqtrade/Alpaca dry-run until a real broker is wired up. Tracks cash,
positions, and a full trade history so P&L is auditable.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from data.provider import fetch_prices

LEDGER_PATH = Path(__file__).resolve().parent.parent / "portfolio.json"
STARTING_CASH = 100_000.0


def _load() -> dict:
    if not LEDGER_PATH.exists():
        return {"cash": STARTING_CASH, "positions": {}, "history": []}
    return json.loads(LEDGER_PATH.read_text())


def _save(state: dict) -> None:
    LEDGER_PATH.write_text(json.dumps(state, indent=2))


def _last_price(ticker: str) -> float:
    prices = fetch_prices(ticker, period="5d", interval="1d")
    return float(prices["Close"].iloc[-1])


def buy(ticker: str, shares: float) -> dict:
    ticker = ticker.upper()
    state = _load()
    price = _last_price(ticker)
    cost = price * shares
    if cost > state["cash"]:
        raise ValueError(f"Insufficient paper cash: need ${cost:,.2f}, have ${state['cash']:,.2f}")
    state["cash"] -= cost
    pos = state["positions"].get(ticker, {"shares": 0.0, "avg_cost": 0.0})
    new_shares = pos["shares"] + shares
    pos["avg_cost"] = (pos["avg_cost"] * pos["shares"] + cost) / new_shares
    pos["shares"] = new_shares
    state["positions"][ticker] = pos
    state["history"].append({"ts": time.time(), "action": "BUY", "ticker": ticker, "shares": shares, "price": price})
    _save(state)
    return {"ticker": ticker, "action": "BUY", "shares": shares, "price": price, "cash_remaining": state["cash"]}


def sell(ticker: str, shares: float) -> dict:
    ticker = ticker.upper()
    state = _load()
    pos = state["positions"].get(ticker)
    if not pos or pos["shares"] < shares:
        held = pos["shares"] if pos else 0.0
        raise ValueError(f"Cannot sell {shares} shares of {ticker}: only hold {held}")
    price = _last_price(ticker)
    proceeds = price * shares
    pos["shares"] -= shares
    state["cash"] += proceeds
    if pos["shares"] <= 1e-9:
        del state["positions"][ticker]
    else:
        state["positions"][ticker] = pos
    state["history"].append({"ts": time.time(), "action": "SELL", "ticker": ticker, "shares": shares, "price": price})
    _save(state)
    return {"ticker": ticker, "action": "SELL", "shares": shares, "price": price, "cash_remaining": state["cash"]}


def status() -> dict:
    state = _load()
    positions = []
    market_value = 0.0
    for ticker, pos in state["positions"].items():
        try:
            price = _last_price(ticker)
        except Exception:
            price = pos["avg_cost"]
        value = price * pos["shares"]
        market_value += value
        positions.append({
            "ticker": ticker,
            "shares": pos["shares"],
            "avg_cost": round(pos["avg_cost"], 2),
            "last_price": round(price, 2),
            "market_value": round(value, 2),
            "unrealized_pl": round((price - pos["avg_cost"]) * pos["shares"], 2),
        })
    return {
        "cash": round(state["cash"], 2),
        "market_value": round(market_value, 2),
        "total_equity": round(state["cash"] + market_value, 2),
        "starting_cash": STARTING_CASH,
        "total_return_pct": round((state["cash"] + market_value - STARTING_CASH) / STARTING_CASH * 100, 2),
        "positions": positions,
    }


def history() -> list[dict]:
    return _load()["history"]


def reset() -> dict:
    state = {"cash": STARTING_CASH, "positions": {}, "history": []}
    _save(state)
    return state
