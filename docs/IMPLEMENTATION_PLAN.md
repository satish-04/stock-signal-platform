# Enterprise implementation plan

## Stage 0 — Governance
Define permitted symbols, strategy allowlist, maximum daily loss, maximum contract quantity, trading hours, event blackout rules, data retention, and who may approve orders.

## Stage 1 — Local platform
Run API, worker, PostgreSQL, Redis, Prometheus and Grafana. Validate mock signals and risk rejection. Exit criterion: deterministic tests pass and restart preserves database data.

## Stage 2 — TradingView
Deploy Pine indicator, HTTPS tunnel and webhook secret. Add idempotency and replay protection. Exit criterion: confirmed alerts arrive once with timestamps under the accepted age limit.

## Stage 3 — Claude
Enable API key, JSON schema validation, retries, budget controls and prompt/version storage. Exit criterion: malformed output cannot produce a signal and every inference is auditable.

## Stage 4 — IBKR read-only
Connect paper TWS/IB Gateway. Implement snapshots, option chain, Greeks, news and account state. Keep order submission disabled. Exit criterion: stale/disconnected data blocks signal generation.

## Stage 5 — Paper execution
Implement defined-risk combo limit orders, cancellation, partial-fill handling and reconciliation. Require manual approval. Exit criterion: at least 100 representative paper signals with measured slippage and no orphan positions.

## Stage 6 — Evaluation
Compare performance against technical-only and news-only baselines. Use walk-forward periods; include transaction costs and spread slippage. Reject strategies with unstable or concentrated results.

## Stage 7 — Restricted live pilot
Use a symbol allowlist, one contract maximum, daily kill switch, human approval and separate live credentials. Live trading remains optional and is not enabled by this scaffold.
