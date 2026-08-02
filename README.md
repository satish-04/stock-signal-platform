# Stock Signal App

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)

A local-first, paper-trading-by-default platform that combines TradingView technical alerts, IBKR market/options data, Claude AI news interpretation, deterministic options selection, and risk controls.

## ⚠️ Safety First

This is a paper-trading platform by default. **No live orders will be submitted without explicit configuration.**

- Default `TRADING_MODE=paper`
- Default `MARKET_DATA_MODE=mock`
- Order submission disabled (`ENABLE_ORDER_SUBMISSION=false`)
- Live trading requires two explicit switches and completed IBKR adapter
- Claude never receives unrestricted order-placement tool

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- PostgreSQL (via Docker)
- Redis (via Docker)
- IBKR account with API access
- Anthropic API key for Claude AI

### Installation

#### Method 1: Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/satish-04/stock-signal-app.git
cd stock-signal-app

# Copy environment file and configure
cp .env.example .env
# Edit .env with your credentials

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api worker

# Run tests
docker-compose run --rm api pytest tests/
```

#### Method 2: Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Create database
createdb stock_signal_app

# Apply migrations
alembic upgrade head

# Start development server
python -m uvicorn app.main:app --reload
```

## 📊 Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ 95% | Core Infrastructure (Docker, DB, Workers) |
| Phase 2 | 🟡 85% | Market Data (IBKR, Technical Indicators) |
| Phase 3 | 🟡 75% | AI (Claude Recommendations, Risk) |
| Phase 4 | ⚪ 0% | Dashboard (React UI) - Not Started |
| Phase 5 | 🟡 60% | Automated Trading (Paper Execution) |
| Phase 6 | ⚪ 5% | Production (Kubernetes, HA) |

See [IMPLEMENTATION_PROGRESS.md](IMPLEMENTATION_PROGRESS.md) for detailed status.

## 🏗️ Architecture

```
                 TradingView
                     │
              MCP + Webhooks
                     │
                     ▼
                 FastAPI
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
      IBKR       PostgreSQL      Redis
        │
        ▼
 Historical Data
        │
        ▼
 Indicator Engine
        │
        ▼
 Technical Signal Engine
        │
        ↓
    Option Selection
        │
        ▼
 Risk / Trade Plan
        │
        ▼
 AI Recommendation
        │
        ▼
   Human Approval
        │
        ▼
   Paper Trading
```

### Services

| Service | Port | Description |
|---------|------|-------------|
| API | 8000 | FastAPI application |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache and queues |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards |

## 📦 Features

### Phase 1: Core Infrastructure ✅
- FastAPI with async support
- PostgreSQL database with Alembic migrations
- Redis caching and message queues
- Docker Compose orchestration
- Background workers for market data and signals

### Phase 2: Market Data Engine 🟡 (85% Complete)
- Real-time IBKR market data
- Historical OHLCV data
- Technical indicators (EMA, SMA, RSI, MACD, ATR, VWAP, Bollinger Bands)
- Dynamic option chain selection with underlying-price-centered strikes
- Multiple expiration support

### Phase 3: AI & Signal Engine 🟡 (75% Complete)
- Technical signal generation with confidence scoring
- Claude AI integration for trade recommendations
- Structured output validation
- Risk management (position sizing, stop loss, daily loss limits)
- Trade plan generation

### Phase 4: Dashboard ⚪ (Not Started)
- React frontend with TypeScript
- Portfolio overview
- Market scanner
- Signal center
- Option chain visualization

### Phase 5: Automated Trading 🟡 (60% Complete)
- Paper trading mode by default
- IBKR order execution
- Risk-adjusted position sizing
- Kill switch and safety controls

### Phase 6: Production ⚪ (Not Started)
- Kubernetes deployment
- CI/CD pipeline
- HA infrastructure

## 🛠️ Configuration

### Environment Variables (.env)

```bash
# Trading Configuration
TRADING_MODE=paper                    # paper, live
MARKET_DATA_MODE=mock                 # mock, real
ENABLE_ORDER_SUBMISSION=false          # Safety switch
ENABLE_LIVE_TRADING=false              # Kill switch

# IBKR Configuration
IBKR_HOST=localhost
IBKR_PORT=7496
IBKR_CLIENT_ID=1

# Claude AI Configuration
ANTHROPIC_API_KEY=your_api_key_here
AI_MODE=mock                           # mock, claude
AI_MODEL=claude-3-5-sonnet

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/stock_signal_app

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# TradingView Webhook
WEBHOOK_SECRET=your_webhook_secret_here
WEBHOOK_PORT=8000

# Logging
LOG_LEVEL=INFO
```

## 🔬 Testing

Run tests using Docker Compose:

```bash
# Run all tests
docker-compose run --rm api pytest

# Run unit tests only
docker-compose run --rm api pytest tests/unit/

# Run integration tests
docker-compose run --rm api pytest tests/integration/
```

## 📈 Current Capabilities

### Working End-to-End Flows:
1. **Historical Data Pipeline**: TWS → IBKR API → Historical Bars
2. **Technical Indicators**: EMA, SMA, RSI, MACD, ATR, VWAP, Bollinger Bands
3. **Option Chain Discovery**: reqSecDefOptParams → expiration → qualified contracts
4. **Signal Generation**: Indicators → Technical Signal Engine → Confidence Scoring
5. **AI Recommendations**: Signal + Claude → Trade Plan

### Recent Milestones:
- ✅ 72 AAPL option contracts retrieved
- ✅ Real IBKR conId for options
- ✅ Entitlement-safe quote callbacks
- ✅ ~0.35s chain discovery

## 🔜 Upcoming Priorities

### Phase 2 Completion:
- Real option quotes with IBKR market data entitlement
- Dynamic strike/expiry selection

### Phase 4 Dashboard:
- Set up React project with Vite
- Design system foundation
- Dashboard MVP (portfolio view)

### Production Deployment:
- CI/CD pipeline
- Kubernetes manifests
- Secrets management

## 📝 API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐳 Docker Images

Build images:
```bash
docker-compose build
```

Run in production mode:
```bash
docker-compose up -d
```

View logs:
```bash
docker-compose logs -f
```

Stop services:
```bash
docker-compose down
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Author

Satishreddy

---

*Last Updated: 2024-12-20*