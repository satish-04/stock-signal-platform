1. Extract and start the project
On your Mac:
cd ~/Downloads
unzip stock-signal-platform.zip
cd stock-signal-platform
Install Docker Desktop for Mac. Docker provides separate installation packages for Apple Silicon and Intel Macs.
Start the project:

./scripts/bootstrap-mac.sh
The script will:
Create .env from .env.example
Generate a strong TradingView webhook secret
Build the containers
Start PostgreSQL, Redis, API, worker, Prometheus and Grafana
Perform an API health check
Verify:
make health
Expected result:
{
  "status": "ok",
  "environment": "local",
  "trading_mode": "paper",
  "market_data_mode": "mock",
  "orders_enabled": false
}
Open:
API documentation: http://localhost:8080/docs
Grafana:          http://localhost:3000
Prometheus:       http://localhost:9090
Grafana’s initial credentials are:
Username: admin
Password: admin
Change the password after first login.
2. Test the complete mock-data workflow
Generate a mock AAPL bullish signal:
make seed
Watch the signal worker:
make logs
You should see a structured event similar to:
{
  "event": "signal_generated",
  "symbol": "AAPL",
  "direction": "bullish",
  "candidate": {
    "strategy": "call_debit_spread",
    "long_conid": 1,
    "short_conid": 2,
    "max_debit": 2.7,
    "max_loss": 270,
    "max_profit": 230
  },
  "risk_approved": true
}
Run tests:
make test
The included tests verify:
Bullish option spread selection
Maximum-loss calculation
Oversized position rejection
Defined-risk enforcement
3. Configure Claude
Open .env:
vi .env
Set:
ANTHROPIC_API_KEY=your-anthropic-api-key
CLAUDE_MODEL=your-supported-claude-model
Restart:
docker compose restart api worker
Claude is used only for:
News classification
Directional interpretation
Materiality analysis
Novelty analysis
Expected impact duration
Risk identification
Thesis invalidation conditions
Claude supports structured tool use and MCP-based integrations, but the project deliberately keeps order execution outside Claude’s unrestricted control.
When no Claude API key is configured, the service returns:

{
  "direction": "neutral",
  "confidence": 0,
  "recommended_bias": "no_trade"
}
This prevents missing credentials from producing an actionable signal.
4. Configure TradingView
The Pine Script is located at:
pine/enterprise_signal.pine
It calculates:
EMA 20
EMA 50
VWAP
RSI
Relative volume
Confirmed-bar bullish signals
Confirmed-bar bearish signals
TradingView supports webhook alerts that send HTTP POST requests to an external endpoint whenever an alert fires.
Add the indicator
Open TradingView.
Open a stock chart.
Open Pine Editor.
Paste the contents of:
pine/enterprise_signal.pine
Select Add to chart.
Create one bullish alert and one bearish alert.
Expose your local webhook
TradingView needs a publicly reachable HTTPS endpoint. Use a tunnel such as Cloudflare Tunnel or another HTTPS reverse tunnel.
Your TradingView URL should end with:

/api/v1/webhooks/tradingview
Example structure:
https://your-random-tunnel.example/api/v1/webhooks/tradingview
TradingView supports HTTPS webhook authentication mechanisms, including certificate validation on the receiver side.
Bullish webhook message
Copy:
config/tradingview-message.json
Replace the secret with the value from .env:
{
  "secret": "YOUR_GENERATED_SECRET",
  "symbol": "{{ticker}}",
  "exchange": "{{exchange}}",
  "timeframe": "{{interval}}",
  "timestamp": "{{timenow}}",
  "close": {{close}},
  "volume": {{volume}},
  "signal": "bullish_breakout",
  "strategy": "ema_vwap_relative_volume",
  "bar_confirmed": true,
  "indicators": {}
}
For the bearish alert, change:
"signal": "bearish_breakdown"
Never place IBKR, Claude or database credentials inside the TradingView message.
5. Configure IBKR paper trading
Install and open either:
Trader Workstation
IB Gateway
Use the paper trading account first.
IBKR permits sharing eligible real-time market-data subscriptions with a paper account, although the shared data generally cannot be consumed simultaneously by both the live and paper usernames.

TWS settings
In TWS:
Open Global Configuration.
Open API.
Open Settings.
Enable socket clients.
Use read-only mode initially.
Restrict trusted IPs to localhost.
Confirm the paper API port.
The project defaults to:
IBKR_HOST=host.docker.internal
IBKR_PORT=7497
IBKR_CLIENT_ID=41
Port 7497 is commonly used for TWS paper mode, but confirm the configured port in your own TWS installation.
Install the official IBKR Python API
IBKR recommends downloading a supported stable or latest TWS API release and installing its Python source package.
After installation, validate Python access:

python3 -c "import ibapi; print('IBKR API available')"
The project’s IBKR boundary is:
app/services/brokers/ibkr.py
Implement the following there:
connect and reconnect
nextValidId handling
contractDetails callbacks
reqMktData
tickPrice
tickSize
tickOptionComputation
reqSecDefOptParams
securityDefinitionOptionParameter
reqNewsProviders
reqHistoricalNews
reqNewsArticle
accountSummary
positions
openOrder
orderStatus
error handling
connectionClosed
IBKR’s current documentation covers market data, historical data, orders, account information and scanners through the TWS API.
After the read-only adapter works:

MARKET_DATA_MODE=ibkr
Restart:
docker compose restart api worker
Do not enable order submission yet.
6. Required IBKR production behavior
The IBKR implementation should maintain a request registry:
request_id -> {
    request_type,
    symbol,
    contract,
    future,
    started_at,
    timeout_at
}
The adapter must block signals when:
IBKR is disconnected
quote timestamp is stale
bid or ask is missing
option Greeks are incomplete
option contract is not qualified
market-data permissions are missing
spread is outside policy
request pacing is exceeded
account state is unavailable
The option-chain flow should be:
Resolve stock contract
→ request option parameters
→ filter expirations
→ filter strike range
→ qualify option contracts
→ request option market data
→ collect Greeks
→ calculate liquidity
→ pass valid contracts to options engine
Do not subscribe to every strike and expiration. Filter before requesting market data.
Suggested initial selection:

DTE: 21–60 days
Strike distance: ±15% from underlying
Maximum expirations: 3
Maximum contracts per symbol: 40
7. News ingestion design
Create a dedicated IBKR news worker under:
app/workers/news_worker.py
Recommended workflow:
IBKR headline received
→ normalize symbol
→ retrieve article where entitled
→ calculate duplicate hash
→ persist raw article
→ send to Claude
→ validate Claude JSON
→ persist analysis
→ publish news-analysis event
Use this deduplication key:
provider
+ provider_article_id
+ normalized headline
+ symbol
Do not send duplicate syndications to Claude.
Prioritize:

Open positions
Active option positions
TradingView signal symbols
Watchlist
Earnings-calendar symbols
High-relative-volume symbols
This is more practical than continuously analyzing every listed U.S. stock.
8. Signal consensus
The project uses this initial score:
35% Claude news confidence
30% TradingView technical confirmation
25% option liquidity and structure quality
10% broader market regime
Recommended thresholds:
strong_candidate: 80
review_candidate: 65
reject_below: 65
No signal should pass unless:
bar is confirmed
news is recent
IBKR quote is fresh
option spread is liquid
maximum loss is known
risk engine approves
signal is not duplicated
daily loss lock is inactive
9. Option strategies
The included project supports the foundation for:
Bullish:
Call debit spread

Bearish:
Put debit spread
Add these later:
Bull put spread
Bear call spread
Long call
Long put
Iron condor
Long straddle
Long strangle
For the first enterprise release, keep only defined-risk vertical spreads.
Never allow:

Naked short calls
Naked short puts
Undefined-risk ratio spreads
Market orders for option combinations
Zero-DTE automated execution
10. Risk policies
Current environment controls:
MAX_RISK_PER_TRADE_PCT=0.50
MAX_DAILY_LOSS_PCT=1.50
MAX_OPEN_POSITIONS=5
SIGNAL_TTL_SECONDS=120
For example, with a $100,000 account:
Maximum risk per trade:
$100,000 × 0.50% = $500
A spread with a maximum loss above $500 is rejected.
Add these controls before paper execution:

Maximum contracts per order
Maximum risk per symbol
Maximum correlated-sector exposure
Maximum total options buying power
Earnings-event restriction
Trading-hours restriction
Minimum DTE
Minimum open interest
Minimum volume
Maximum bid/ask spread
Maximum daily realized loss
Maximum daily unrealized loss
Emergency kill switch
11. Order workflow
The correct workflow is:
Signal generated
→ risk approved
→ notification sent
→ user approves
→ IBKR quote refreshed
→ risk recalculated
→ limit price constructed
→ combo limit order submitted
→ order status monitored
→ partial fills reconciled
→ position persisted
Do not use the original signal quote after human approval. Refresh the stock and all option legs immediately before submission.
Recommended limit behavior:

Initial debit = spread midpoint
Maximum debit = policy-defined ceiling
Adjustment interval = 5–10 seconds
Maximum adjustments = 2 or 3
Cancel if signal expires
Never automatically cross an excessive spread
12. Enable paper order submission
Only after completing the IBKR adapter:
TRADING_MODE=paper
MARKET_DATA_MODE=ibkr
ENABLE_ORDER_SUBMISSION=true
ENABLE_LIVE_TRADING=false
The combination means:
Real IBKR paper data
Paper orders permitted
Live trading impossible
Keep the TWS account logged into paper mode.
13. Live-trading protection
The project requires two separate live switches:
TRADING_MODE=live
ENABLE_ORDER_SUBMISSION=true
ENABLE_LIVE_TRADING=true
The application refuses to start in live mode unless both order flags are explicitly enabled.
Before any live pilot, also require:

Manual approval
Symbol allowlist
One-contract maximum
Defined-risk spreads only
Daily loss lock
Paper-performance review
Separate live configuration
Separate client ID
Separate database environment
Verified kill switch
14. Project structure
stock-signal-platform/
├── app/
│   ├── api/routes/
│   │   ├── health.py
│   │   ├── webhooks.py
│   │   └── dev.py
│   ├── core/
│   │   ├── config.py
│   │   └── logging.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   └── entities.py
│   ├── schemas/
│   │   └── events.py
│   ├── services/
│   │   ├── brokers/
│   │   │   ├── base.py
│   │   │   ├── factory.py
│   │   │   ├── mock.py
│   │   │   └── ibkr.py
│   │   ├── llm/
│   │   │   └── claude.py
│   │   ├── options/
│   │   │   └── engine.py
│   │   ├── risk/
│   │   │   └── engine.py
│   │   └── signals/
│   │       └── engine.py
│   ├── workers/
│   │   └── signal_worker.py
│   └── main.py
├── config/
│   └── tradingview-message.json
├── docs/
│   └── IMPLEMENTATION_PLAN.md
├── grafana/
├── pine/
│   └── enterprise_signal.pine
├── prometheus/
├── scripts/
│   └── bootstrap-mac.sh
├── tests/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
└── README.md
Recommended next implementation milestone
Complete the IBKR adapter in this order:
1. Connection management
2. Stock contract qualification
3. Stock snapshots
4. Option expiration and strike discovery
5. Option quote and Greek collection
6. IBKR news ingestion
7. Account and position retrieval
8. Database persistence
9. Manual approval endpoint
10. Paper combination orders
The downloaded project provides the local enterprise foundation and safely runnable mock workflow. Real IBKR market data and paper order execution require completing app/services/brokers/ibkr.py against your installed official TWS API and your account’s subscriptions.
