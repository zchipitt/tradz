# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tradz is a daily trading signal aggregation system that collects data from multiple sources, generates quantitative signals with 4-dimensional scoring, and delivers reports via email. It includes:
- **Core Pipeline**: Data aggregation, entity resolution, signal generation, and email reports
- **DuckDB Database**: Persistent storage for entities, observations, events, and signals
- **Web Dashboard**: React frontend with FastAPI backend for interactive visualization

## Common Commands

```bash
# Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run nightly signal generation (full pipeline)
python3 src/tradz/run_nightly.py

# Run with Claude report generation
python3 src/tradz/run_nightly.py --use-claude

# Run with template only (skip Claude)
python3 src/tradz/run_nightly.py --template-only

# Run without sending email
python3 src/tradz/run_nightly.py --skip-email

# Force entity refresh from SEC
python3 src/tradz/run_nightly.py --refresh-entities

# Run via shell script (for cron)
./scripts/nightly.sh

# One-click local development
./scripts/local_up.sh    # Start backend (8002) + frontend (5173)
./scripts/local_down.sh  # Stop all services

# Manual API/frontend startup
uvicorn api.main:app --reload --port 8002
cd frontend && npm install && npm run dev

# Verification scripts
python3 scripts/verify_db.py       # Verify database schema
python3 scripts/verify_entities.py # Verify entity resolution
python3 scripts/verify_signals.py  # Verify signal generation
python3 scripts/verify_facts.py    # Verify fact generation

# Debug scripts
python3 scripts/debug_server_error.py   # Debug API server errors
python3 scripts/debug_yfinance.py       # Debug yfinance data fetching
python3 scripts/test_news_fetch.py      # Test news source fetching
python3 scripts/test_polymarket_fetch.py # Test Polymarket API
```

## Project Structure

```
tradz/
├── src/tradz/                    # Core Python backend
│   ├── sources/                  # Data source fetchers
│   │   ├── equities.py           # yfinance integration
│   │   ├── crypto.py             # ccxt multi-exchange (Kraken default)
│   │   ├── congress.py           # Congressional trades (Capitol Trades + fallbacks)
│   │   ├── hedgefunds.py         # SEC 13F filings
│   │   ├── polymarket.py         # Prediction markets
│   │   ├── news.py               # NewsAPI + Yahoo Finance fallback
│   │   ├── sec_filings.py        # SEC EDGAR filings
│   │   └── brokers/              # Broker integrations
│   │       ├── base.py           # Base broker interface
│   │       └── ibkr.py           # Interactive Brokers (optional)
│   ├── events/                   # Event-driven system (vNext)
│   │   ├── builder.py            # EventBuilder: aggregates observations into events
│   │   ├── fact_extractor.py     # Extracts FactTableEntry from observations
│   │   ├── llm_provider.py       # LLM abstraction (Claude CLI, OpenRouter, Mock)
│   │   └── title_generator.py    # LLM title generation with template fallback
│   ├── reporting/                # Report generation
│   │   └── fact_generator.py     # Deterministic fact extraction for LLM
│   ├── models.py                 # Core data models (Entity, Observation, Event, Signal, FactType)
│   ├── database.py               # DuckDB persistence layer
│   ├── entity_resolver.py        # Ticker/CIK/Name mapping
│   ├── scoring.py                # 4-dimensional signal scoring
│   ├── signals.py                # Signal generation
│   ├── aggregator.py             # Multi-source orchestration
│   ├── report.py                 # Template-based reports
│   ├── claude_reporter.py        # Claude CLI integration
│   ├── emailer.py                # SMTP email delivery
│   └── run_nightly.py            # Main entry point
├── api/                          # FastAPI backend
│   ├── main.py                   # App entry point
│   ├── config.py                 # API settings
│   ├── routers/                  # REST endpoints
│   │   ├── signals.py            # Signal endpoints
│   │   ├── sources.py            # Data source endpoints
│   │   ├── reports.py            # Report endpoints
│   │   ├── events.py             # Event endpoints (list, detail, actions)
│   │   └── system.py             # System status endpoint
│   ├── schemas/                  # Pydantic models
│   │   ├── signals.py
│   │   ├── sources.py
│   │   ├── events.py             # Event request/response schemas
│   │   └── system.py             # System health schemas
│   └── services/                 # Business logic
│       ├── signal_service.py     # Signal caching (5-min TTL)
│       ├── aggregator_service.py # Data aggregation
│       ├── cache_service.py      # In-memory caching
│       ├── event_service.py      # Event queries and actions
│       └── system_service.py     # System health checks
├── frontend/                     # React + TypeScript
│   └── src/
│       ├── App.tsx               # Root with TanStack Query
│       ├── pages/                # Page components
│       │   ├── Dashboard.tsx     # Event-centric main view
│       │   ├── Signals.tsx       # Raw signals table
│       │   ├── Sources.tsx       # Source panels
│       │   ├── Reports.tsx       # Report archive
│       │   └── UsageGuide.tsx    # Interactive guide
│       ├── components/
│       │   ├── layout/Layout.tsx # Header + sidebar + tabs
│       │   ├── events/           # Event components (EventCard, SignalInbox, SystemStatus)
│       │   ├── signals/          # Signal components
│       │   └── sources/          # Source panels
│       ├── hooks/                # React Query hooks
│       │   ├── useSignals.ts     # 5-min auto-refresh
│       │   ├── useEvents.ts      # Event actions + useSystemStatus
│       │   └── useSources.ts     # Source health
│       └── api/                  # API client
│           ├── client.ts         # Axios + API functions
│           └── types.ts          # TypeScript interfaces
├── tests/                        # Unit tests
│   ├── test_event_builder.py    # EventBuilder tests
│   ├── test_events_api.py       # Events API tests
│   ├── test_fact_extractor.py   # Fact extraction tests
│   ├── test_llm_provider.py     # LLM provider tests
│   ├── test_system_api.py       # System API tests
│   └── test_title_generator.py  # Title generation tests
├── scripts/                      # Utility scripts
│   ├── ralph/                    # Autonomous AI agent
│   │   ├── ralph.sh              # Agent loop script
│   │   ├── CLAUDE.md             # Agent instructions
│   │   └── progress.txt          # Agent progress log
│   └── ...                       # Other scripts
├── tasks/                        # Development tasks
│   └── prd-tradz-vnext.md        # Product requirements document
├── prd.json                      # PRD with user stories (for Ralph agent)
├── data/                         # DuckDB + JSON data
├── reports/                      # Generated reports
├── prompts/                      # Claude AI prompts
├── config.yaml                   # Configuration
└── requirements.txt              # Python dependencies
```

## Architecture

### Data Flow
```
DataAggregator → EntityResolver → Scorer → SignalGenerator → ReportGenerator → EmailSender
      ↓               ↓              ↓            ↓
   DuckDB:        entities      observations   signals
                                  events
      ↓
  API (FastAPI) → Frontend (React)
```

### Core Components

**Entry Point**: `src/tradz/run_nightly.py`
- 4-step process: aggregate → generate signals → create report → send email
- CLI flags: `--use-claude`, `--template-only`, `--skip-email`, `--refresh-entities`

**Data Models** (`src/tradz/models.py`):
- `Entity` - Ticker/CIK/Name mappings with aliases
- `Observation` - Raw data points with quality/freshness scores
- `Event` - Aggregated stories linking observations
- `Signal` - 4-dimensional scored output (anomaly, catalyst, flow, confidence)
- `FactTable` / `FactTableEntry` - Deterministic facts for LLM (prevents AI fabrication)

**Database Layer** (`src/tradz/database.py`):
- DuckDB persistence at `data/tradz.duckdb`
- Tables: `entities`, `observations`, `events`, `signals`, `event_observations`, `run_history`
- Singleton pattern via `get_database()`

**Entity Resolution** (`src/tradz/entity_resolver.py`):
- Resolves tickers/CIKs/names to unique Entity IDs
- Syncs SEC ticker data (`company_tickers.json`)
- In-memory caching for fast lookups

**Scoring** (`src/tradz/scoring.py`):
- 4-dimensional scoring (0-100 each):
  - `anomaly_score`: Z-scores for price (40%), volume (30%), volatility (20%)
  - `catalyst_score`: SEC filings, news, Polymarket events
  - `flow_score`: Congress trades, 13F filings
  - `confidence_score`: Data quality and source verification
- Composite: `attention_score = 0.3×anomaly + 0.3×catalyst + 0.25×flow + 0.15×confidence`

**Data Sources** (`src/tradz/sources/`):
| Source | File | Description |
|--------|------|-------------|
| Equities | `equities.py` | US stocks via yfinance (60-day history) |
| Crypto | `crypto.py` | Multi-exchange via ccxt (Binance → Coinbase → Kraken) |
| Congress | `congress.py` | Capitol Trades (free) → Quiver → Finnhub |
| Hedge Funds | `hedgefunds.py` | SEC EDGAR 13F filings |
| Polymarket | `polymarket.py` | Prediction market odds |
| News | `news.py` | NewsAPI → Yahoo Finance fallback |
| SEC Filings | `sec_filings.py` | 10-K, 10-Q, 8-K forms |
| IBKR | `brokers/ibkr.py` | Interactive Brokers (optional) |

### Web Dashboard

**API Endpoints** (`api/`):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/signals` | GET | All signals (optional `?refresh=true`) |
| `/api/signals/top` | GET | Top 5 equity + crypto |
| `/api/signals/{symbol}` | GET | Single signal |
| `/api/events` | GET | Event list with status/sort/pagination |
| `/api/events/{event_id}` | GET | Event detail with observations |
| `/api/events/{event_id}/actions` | POST | Event actions (pin/unpin/snooze/dismiss/resolve) |
| `/api/system/status` | GET | Data source health status |
| `/api/sources` | GET | All source data |
| `/api/sources/equities` | GET | Equities data |
| `/api/sources/crypto` | GET | Crypto data |
| `/api/sources/congress` | GET | Congress trades |
| `/api/sources/hedgefunds` | GET | 13F filings |
| `/api/sources/polymarket` | GET | Prediction markets |
| `/api/sources/news` | GET | News articles |
| `/api/sources/sec` | GET | SEC filings |
| `/api/reports` | GET | Historical reports |
| `/api/reports/latest` | GET | Most recent report |
| `/api/reports/{date}` | GET | Report by date (YYYY-MM-DD) |

**Frontend** (`frontend/`):
- **Tech**: React 18 + TypeScript + Vite + TanStack Query + Tailwind CSS
- **Design**: Robinhood-style clean interface, event-centric
- **Pages**:
  - `Dashboard` - Event-centric with 4 sections: SystemStatus, SignalInbox, DailyBrief, MarketSnapshot
  - `Signals` - Raw diagnostic table
  - `Sources` - Individual source panels (Congress, HedgeFunds, News, Polymarket)
  - `Reports` - Historical archive with Markdown viewer
  - `UsageGuide` - Interactive collapsible guide
- **Event Components**:
  - `EventCard` - 4D scores, evidence, trade plan
  - `SignalInbox` - Filtered list (Active/Resolved/All)
  - `SystemStatus` - Data quality overview
  - `DailyBrief` - Summary + trade ideas
  - `MarketSnapshot` - Collapsible heatmap

**Event State Machine**:
- `new` → `ongoing` → `stale` (no updates 72h+)
- User actions: `resolved`, `dismissed`
- Actions: Pin/Unpin, Snooze (24h), Resolve, Dismiss

### Configuration

**`config.yaml`**:
```yaml
equities:
  tickers: [AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, JPM, BAC, GS, JNJ, UNH, SPY, QQQ]

crypto:
  exchange: "kraken"  # Default exchange (kraken/binance/coinbase)
  pairs: [BTC/USDT, ETH/USDT, BNB/USDT, SOL/USDT, ADA/USDT, XRP/USDT, DOGE/USDT, AVAX/USDT, MATIC/USDT, DOT/USDT]

thresholds:
  day_return_high: 5.0
  week_return_high: 10.0
  volume_high: 2.0

congress:
  enabled: true
  lookback_days: 30
  min_amount: 15000

hedgefunds:
  enabled: true
  min_position_change_pct: 25.0
  notable_funds: [Berkshire, Citadel, Renaissance, Tiger Global, Bridgewater, Pershing Square...]

polymarket:
  enabled: true
  categories: [Economy, Crypto, Business, Politics, Finance, Stocks, Tech]
  max_markets: 20

claude:
  enabled: true
  timeout: 300
  fallback_to_template: true
```

**`.env`**: Sensitive credentials
- `DRY_RUN=1` - Prevents actual email sending
- `SMTP_*` - Email configuration
- `ANTHROPIC_API_KEY` - For Claude Code CLI
- `OPENROUTER_API_KEY` - Alternative LLM provider for title generation
- `NEWSAPI_KEY` - Optional, falls back to Yahoo
- `QUIVER_API_KEY`, `FINNHUB_API_KEY` - Optional fallbacks

### Output Files

- `reports/{date}.md` - Markdown report
- `reports/{date}.json` - Raw signals
- `data/{date}.json` - Aggregated source data
- `data/tradz.duckdb` - Persistent database

## Key Patterns

- **Data Sources**: Common interface with `fetch_data()`, `get_latest_data()`, `close()`
- **Multi-Source Fallback**: Congress tries 3 sources sequentially
- **Retry Logic**: Exponential backoff in all data sources
- **Singleton Pattern**: Database via `get_database()`
- **Fact-Constrained LLM**: FactTable prevents AI fabrication in reports
- **Dual-Channel Reporting**: Template fallback ensures reports always generated
- **Entity Resolution**: Canonical ID mapping across all sources
- **4D Scoring**: Composite `attention_score = 0.3×anomaly + 0.3×catalyst + 0.25×flow + 0.15×confidence + coverage_bonus`
- **Coverage Bonus**: +5 per unique source, max +20
- **Services Layer**: Business logic abstracted from route handlers
- **TanStack Query**: 5-minute auto-refresh with caching
- **Event State Machine**: 5-state tracking (new → ongoing → stale, resolved, dismissed)
- **LLM Providers**: Abstract base class pattern with `generate()` method (ClaudeCLI, OpenRouter, Mock)
- **Title Generation**: Returns `(title, source)` tuple where source is 'llm' or 'template'
- **Fact Extraction**: Use `FactType` enum (23 types) via `extract_facts(observation)`
- **API Tests**: Use `from api.routers.X import router` and `TestClient(app)` pattern
- **Action Labels**: Confidence thresholds - >=70: Act (green), >=40: Investigate (yellow), <40: Monitor (gray)
- **Daily Brief Persistence**: Use `DailyBriefPersister.persist()` for idempotent save to files and database:
  - Files saved to `reports/{YYYY-MM-DD}.md` (markdown) and `reports/{YYYY-MM-DD}.json` (structured data)
  - Database insert uses UPSERT (ON CONFLICT UPDATE) for idempotent regeneration
  - Link to run_history via optional `run_id` parameter
  - Generation method tracked ('claude' or 'template') for monitoring

## Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_event_builder.py

# Run with verbose output
pytest -v tests/

# Run tests matching pattern
pytest -k "test_build_events" tests/
```
