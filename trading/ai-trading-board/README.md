# AI Trading Board

A local CLI that ties together the four layers described in the vault's
`ai-trading-platform-plan.md`, scoped down from the full FastAPI+Next.js
dashboard to something you can run and use today:

1. **Data** — yfinance (free, no API key)
2. **Analysis** — a composite 0–100 Trade Score (technical + fundamental +
   sentiment + risk), in the spirit of the `zubair-trabzada-ai-trading-hermes`
   toolkit referenced in the vault
3. **Backtesting** — VectorBT, single-run or full parameter sweeps
4. **Execution** — a simulated paper-trading ledger (stand-in for
   Freqtrade/Alpaca dry-run)

No live trading, no exchange keys, no real money — this is a research and
paper-trading tool.

## Setup

```bash
cd ai-trading-board
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Tested on Python 3.14 (macOS). If VectorBT/numba fail to build on your
Python version, use Python 3.11–3.13 instead.

## Usage

### Analyze a stock

```bash
python cli.py analyze AAPL
```

Prints a composite Trade Score (0–100) with a Strong Buy/Buy/Hold/Caution/Avoid
grade, plus the reasoning behind each sub-score:

- **Technical (30%)** — trend (MA50/MA200), momentum (RSI, MACD), volatility (Bollinger Band width)
- **Fundamental (30%)** — P/E, revenue growth, profit margin, debt/equity
- **Sentiment (20%)** — keyword polarity across recent headlines
- **Risk (20%)** — annualized volatility, 1y max drawdown, return skew

Use `python cli.py analyze AAPL --json` to export the same analysis as JSON. After
review, import that file from the platform repository root with
`scripts/import_research.py --symbol AAPL --provider ai-trading-board`; the platform
stores it as attributed research context and still applies its own risk controls.

### Backtest a strategy

```bash
# Single run with specific params
python cli.py backtest AAPL --strategy ma_cross --fast 10 --slow 50

# Sweep parameters, ranked by Sharpe ratio
python cli.py backtest AAPL --strategy ma_cross --sweep
python cli.py backtest AAPL --strategy rsi --sweep
```

### Paper trade

```bash
python cli.py paper buy AAPL 10
python cli.py paper sell AAPL 5
python cli.py paper status
python cli.py paper history
python cli.py paper reset      # back to $100,000 cash
```

Portfolio state lives in `portfolio.json` (gitignored) at the project root.

## Project layout

```
ai-trading-board/
├── data/provider.py           # yfinance wrapper (swap providers here later)
├── analysis/
│   ├── technical.py           # trend/momentum/volatility scoring
│   ├── fundamental.py         # valuation/growth/profitability scoring
│   ├── sentiment.py           # headline keyword polarity scoring
│   ├── risk.py                # volatility/drawdown scoring
│   └── score.py                # weighted composite Trade Score
├── backtest/vectorbt_backtest.py  # MA crossover + RSI reversion, single-run + sweep
├── execution/paper_broker.py  # JSON-backed simulated portfolio
├── cli.py                     # entrypoint
└── requirements.txt
```

## Known limitations

- **Sentiment is a lexicon heuristic**, not real NLP — treat it as a rough
  directional nudge, not ground truth. Swap in FinBERT if you want a real model.
- **Fundamentals come from yfinance's `.info`**, which is best-effort and
  sometimes sparse for smaller tickers or non-US listings.
- **Paper broker uses daily close prices**, not live fills — fine for
  directional tracking, not for testing execution quality.
- **No persistence beyond the local JSON file** — this is a single-user,
  single-machine tool, not the multi-user dashboard described in the
  full plan.

## Where this fits in the bigger plan

This covers Phase 0–1 of `../ai-trading-platform-plan.md` (data lake →
VectorBT backtests → signal generation) plus a minimal stand-in for the
Phase 1 executor, all as a CLI instead of FastAPI+Next.js+Docker. If/when
you want the web dashboard, real-time WebSocket feed, or actual
Freqtrade/Alpaca paper trading, that's the next layer up — this project's
`analysis/score.py` and `backtest/vectorbt_backtest.py` are the pieces
that would get wrapped in FastAPI endpoints rather than rewritten.
