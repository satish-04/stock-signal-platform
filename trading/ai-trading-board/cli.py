#!/usr/bin/env python
"""AI Trading Board CLI — data, analysis, backtesting, and paper trading in one place.

Usage:
    python cli.py analyze AAPL
    python cli.py backtest AAPL --strategy ma_cross
    python cli.py backtest AAPL --strategy ma_cross --sweep
    python cli.py backtest AAPL --strategy rsi --sweep
    python cli.py paper buy AAPL 10
    python cli.py paper sell AAPL 5
    python cli.py paper status
    python cli.py paper history
    python cli.py paper reset
"""
from __future__ import annotations

import argparse
import json
import sys

from rich.console import Console
from rich.table import Table

console = Console()


def cmd_analyze(args: argparse.Namespace) -> None:
    from analysis.score import analyze_ticker

    with console.status(f"Analyzing {args.ticker.upper()}..."):
        result = analyze_ticker(args.ticker)

    if args.json:
        print(json.dumps(result, indent=2, default=_json_default))
        return

    console.print(f"\n[bold]{result['company_name']} ({result['ticker']})[/bold]")
    console.print(f"[bold cyan]Trade Score: {result['composite_score']}/100 — {result['grade']}[/bold cyan]\n")

    table = Table(title="Sub-Scores")
    table.add_column("Category")
    table.add_column("Score", justify="right")
    table.add_column("Weight", justify="right")
    for cat, w in result["weights"].items():
        score = result["sub_scores"].get(cat)
        table.add_row(cat.capitalize(), f"{score}" if score is not None else "n/a", f"{int(w*100)}%")
    console.print(table)

    for section in ("technical", "fundamental", "sentiment", "risk"):
        console.print(f"\n[bold]{section.capitalize()}[/bold]")
        for note in result[section]["notes"]:
            console.print(f"  - {note}")

    console.print(
        "\n[dim]Not financial advice. Composite score is a heuristic blend of "
        "technical, fundamental, sentiment, and risk signals.[/dim]"
    )


def _json_default(value: object) -> object:
    if hasattr(value, "item"):
        return value.item()
    return str(value)


def cmd_backtest(args: argparse.Namespace) -> None:
    from data.provider import fetch_prices
    from backtest import vectorbt_backtest as bt

    prices = fetch_prices(args.ticker, period=args.period, interval="1d")

    if args.strategy == "ma_cross":
        if args.sweep:
            with console.status("Sweeping MA crossover params..."):
                results = bt.sweep_ma_crossover(prices)
            _print_sweep(f"MA Crossover — {args.ticker.upper()} top params by Sharpe", results)
        else:
            result = bt.run_ma_crossover(prices, fast_window=args.fast, slow_window=args.slow)
            _print_single(args.ticker, result)
    elif args.strategy == "rsi":
        if args.sweep:
            with console.status("Sweeping RSI reversion params..."):
                results = bt.sweep_rsi_reversion(prices)
            _print_sweep(f"RSI Reversion — {args.ticker.upper()} top params by Sharpe", results)
        else:
            result = bt.run_rsi_reversion(prices)
            _print_single(args.ticker, result)
    else:
        console.print(f"[red]Unknown strategy: {args.strategy}[/red]")
        sys.exit(1)


def _print_single(ticker: str, result: dict) -> None:
    console.print(f"\n[bold]{ticker.upper()} — {result['strategy']}[/bold]  params={result['params']}")
    for k, v in result.items():
        if k in ("strategy", "params"):
            continue
        console.print(f"  {k}: {v}")


def _print_sweep(title: str, results: list[dict]) -> None:
    table = Table(title=title)
    table.add_column("Params")
    table.add_column("Return %", justify="right")
    table.add_column("Sharpe", justify="right")
    table.add_column("Max DD %", justify="right")
    table.add_column("Trades", justify="right")
    for r in results:
        table.add_row(str(r["params"]), str(r["total_return_pct"]), str(r["sharpe_ratio"]), str(r["max_drawdown_pct"]), str(r["num_trades"]))
    console.print(table)


def cmd_paper(args: argparse.Namespace) -> None:
    from execution import paper_broker as broker

    if args.action == "buy":
        result = broker.buy(args.ticker, args.shares)
        console.print(f"[green]Bought {result['shares']} {result['ticker']} @ ${result['price']:.2f}[/green] — cash remaining: ${result['cash_remaining']:,.2f}")
    elif args.action == "sell":
        result = broker.sell(args.ticker, args.shares)
        console.print(f"[yellow]Sold {result['shares']} {result['ticker']} @ ${result['price']:.2f}[/yellow] — cash remaining: ${result['cash_remaining']:,.2f}")
    elif args.action == "status":
        s = broker.status()
        console.print(f"\nCash: ${s['cash']:,.2f}   Market Value: ${s['market_value']:,.2f}   Total Equity: ${s['total_equity']:,.2f}")
        console.print(f"Total Return: {s['total_return_pct']}%\n")
        if s["positions"]:
            table = Table(title="Positions")
            for col in ("Ticker", "Shares", "Avg Cost", "Last Price", "Market Value", "Unrealized P/L"):
                table.add_column(col, justify="right" if col != "Ticker" else "left")
            for p in s["positions"]:
                table.add_row(p["ticker"], str(p["shares"]), f"${p['avg_cost']}", f"${p['last_price']}", f"${p['market_value']}", f"${p['unrealized_pl']}")
            console.print(table)
        else:
            console.print("[dim]No open positions.[/dim]")
    elif args.action == "history":
        for h in broker.history():
            console.print(f"{h['action']:4s} {h['shares']:>10} {h['ticker']:6s} @ ${h['price']:.2f}")
    elif args.action == "reset":
        broker.reset()
        console.print("[dim]Paper portfolio reset to $100,000 cash.[/dim]")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Trading Board CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_analyze = sub.add_parser("analyze", help="Run the composite Trade Score analysis on a ticker")
    p_analyze.add_argument("ticker")
    p_analyze.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    p_analyze.set_defaults(func=cmd_analyze)

    p_backtest = sub.add_parser("backtest", help="Backtest a strategy with VectorBT")
    p_backtest.add_argument("ticker")
    p_backtest.add_argument("--strategy", choices=["ma_cross", "rsi"], default="ma_cross")
    p_backtest.add_argument("--sweep", action="store_true", help="Run a parameter sweep instead of a single backtest")
    p_backtest.add_argument("--fast", type=int, default=10, help="Fast MA window (single-run mode)")
    p_backtest.add_argument("--slow", type=int, default=50, help="Slow MA window (single-run mode)")
    p_backtest.add_argument("--period", default="2y", help="History window, e.g. 1y/2y/5y")
    p_backtest.set_defaults(func=cmd_backtest)

    p_paper = sub.add_parser("paper", help="Simulated paper trading ledger")
    paper_sub = p_paper.add_subparsers(dest="action", required=True)
    p_buy = paper_sub.add_parser("buy")
    p_buy.add_argument("ticker")
    p_buy.add_argument("shares", type=float)
    p_sell = paper_sub.add_parser("sell")
    p_sell.add_argument("ticker")
    p_sell.add_argument("shares", type=float)
    paper_sub.add_parser("status")
    paper_sub.add_parser("history")
    paper_sub.add_parser("reset")
    p_paper.set_defaults(func=cmd_paper)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
