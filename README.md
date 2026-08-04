# Stock Signal Platform

A local-first, paper-trading-by-default platform that combines TradingView technical alerts, IBKR market/options data, Claude news interpretation, deterministic options selection, and risk controls.

## Safety boundary

- Default `TRADING_MODE=paper`
- Default `MARKET_DATA_MODE=mock`
- Order submission disabled
- Live trading requires two explicit switches and a completed IBKR adapter
- Claude never receives an unrestricted order-placement tool

## Start on macOS

1. Install Docker Desktop.
2. Open Terminal in this directory.
3. Run:

```bash
./scripts/bootstrap-mac.sh
```

4. Verify:

```bash
make health
make seed
make logs
```

Services:

- API/OpenAPI: http://localhost:8080/docs
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (`admin` / `admin`; change immediately)
- PostgreSQL: localhost:5432
- Redis: localhost:6379

## Dashboard

A React + TypeScript + Vite dashboard lives in `frontend/`, covering signals, positions/portfolio, options, market charts, risk/AI trade planning, orders, trading workflows, and background jobs — responsive across desktop and mobile.

Local development (fastest iteration, hot reload):

```bash
cd frontend
cp .env.example .env      # VITE_API_BASE_URL, defaults to http://localhost:8080
npm install
npm run dev                # http://localhost:5175
```

The API must allow the dashboard's origin via CORS — set `CORS_ALLOWED_ORIGINS` in the root `.env` (defaults to `http://localhost:5175,http://localhost:8090`).

Via Docker Compose (serves the production build through nginx):

```bash
docker compose up -d --build frontend
```

Then open http://localhost:8090. Enter an account ID in the top bar to load positions/portfolio/workflows (the backend has no "list accounts" endpoint — accounts are free-form strings). Seed sample signals with `make seed` to populate the Signals and Overview pages.

Note: ports 5175 (dev) and 8090 (Docker) were chosen because 5173/5174, Vite's usual default range, are already occupied by stray dev-server processes from another local project.

## Claude

Add `ANTHROPIC_API_KEY` to `.env`. The service uses structured JSON classification. When absent, it fails safely to neutral/no-trade analysis.

## TradingView

1. Paste `pine/enterprise_signal.pine` into Pine Editor and add it to a chart.
2. Create alerts on the indicator conditions.
3. Expose local port 8080 with an HTTPS tunnel.
4. Set webhook URL to `https://YOUR-TUNNEL/api/v1/webhooks/tradingview`.
5. Use `config/tradingview-message.json`, replacing the secret and signal name.
6. Create separate bullish and bearish alerts so each sends the correct `signal` value.

Never place credentials in the TradingView message.

## IBKR paper integration

1. Install TWS or IB Gateway.
2. Log into the paper account.
3. Enable API socket clients in settings.
4. Use paper port 7497 for TWS or the configured IB Gateway paper port.
5. Restrict trusted IPs to localhost.
6. Install the official TWS Python API.
7. Implement `app/services/brokers/ibkr.py` using:
   - contract qualification
   - `reqMktData`
   - `reqSecDefOptParams`
   - option computation ticks
   - news providers/headlines/articles
   - combo-order submission only after paper validation
8. Change `MARKET_DATA_MODE=ibkr` only after tests pass.

## Event flow

```text
TradingView webhook -> Redis technical-signals -> worker
-> Claude classification -> broker option chain -> deterministic spread selection
-> risk policy -> Redis trade-signals -> notification/dashboard adapter
```

## Development commands

```bash
make up
make down
make logs
make test
make lint
make seed
```

## Production-hardening backlog

- Alembic migrations instead of startup schema creation
- OIDC login and role-based access
- macOS Keychain or Vault secrets
- IBKR adapter with reconnect, pacing, request correlation and stale-data detection
- Separate news ingestion worker
- Postgres persistence for every input, analysis, decision and order event
- Notification adapter for Slack/Telegram/email
- Manual approval UI
- Backtesting and walk-forward evaluation
- Kill switch, daily-loss lock, symbol allowlist and trading-hours policy
- Signed webhook gateway and replay cache
- Encrypted backups and restore tests
- CI security scanning, SBOM and pinned image digests

## Signal persistence and thresholds

Every evaluated technical event is now persisted in PostgreSQL, together with its risk decision.
The default policy is:

- score below 65: `rejected`
- score from 65 through 79.99: `review`
- score 80 or higher, with risk approval: `actionable`

Inspect recent signals:

```bash
make signals
```

Or query directly:

```bash
curl -s 'http://localhost:8080/api/v1/signals?limit=20' | python3 -m json.tool
curl -s 'http://localhost:8080/api/v1/signals?status=rejected&symbol=AAPL' | python3 -m json.tool
```


## Testing

The Docker image includes the project development dependencies so tests and static checks run reproducibly inside the container.

```bash
make test
make lint
```


## v0.3 technical scoring engine

TradingView alerts now carry the actual indicator evidence used by the deterministic scorer. The technical score is 0-100:

- EMA alignment: 25 points
- Price versus VWAP: 20 points
- Direction-aware RSI confirmation: 20 points
- Relative volume: 20 points
- 15-minute and 60-minute trend confirmation: 15 points

Every PostgreSQL signal record includes `details.score_components` and `details.technical_analysis`, including individual component points, raw evidence, and warnings. Missing data fails closed and receives no points.

Exercise the profiles locally:

```bash
curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=weak' | python3 -m json.tool
curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=strong' | python3 -m json.tool
curl -fsS -X POST 'http://localhost:8080/api/v1/dev/seed?profile=bearish' | python3 -m json.tool
sleep 2
make signals
```

For TradingView, replace the webhook secret in the Pine indicator settings, create one alert using **Any alert() function call**, and use the platform webhook URL. The script constructs the JSON dynamically; do not paste a static alert body.

Phase 1 ✅ Infrastructure
────────────────────────
✔ Docker
✔ PostgreSQL
✔ Redis
✔ FastAPI
✔ Worker
✔ Prometheus
✔ Grafana

Phase 2 ✅ Market Data
──────────────────────
✔ TradingView MCP
✔ IBKR API
✔ Historical candles
✔ Option chains

Phase 3 (Next)
──────────────────────
□ Technical indicator engine
□ Signal engine
□ Strategy engine
□ Risk engine

Phase 4
──────────────────────
□ Paper trading
□ Position manager
□ Portfolio manager

Phase 5
──────────────────────
□ Claude AI reasoning
□ News analysis
□ Multi-agent consensus

Phase 6 ✅ Dashboard
──────────────────────
✔ React Dashboard
✔ Live charts
✔ Option chain
✔ Portfolio
□ Watchlist

Phase 7
──────────────────────
□ Production deployment
□ Kubernetes
□ Monitoring
□ Secrets