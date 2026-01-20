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
- Orchestrates the full pipeline: load config → aggregate data → resolve entities → generate signals → create report → send email

**Data Models** (`src/tradz/models.py`):
- `Entity` - Ticker/CIK/Name mappings with aliases
- `Observation` - Raw data points from sources with quality/freshness scores
- `Event` - Aggregated trackable stories linking observations
- `Signal` - 4-dimensional scored output (anomaly, catalyst, flow, confidence)
- `FactTable` / `FactTableEntry` - Deterministic facts for LLM reporting

**Database Layer** (`src/tradz/database.py`):
- DuckDB-based persistence at `data/tradz.duckdb`
- Tables: `entities`, `observations`, `events`, `signals`, `event_observations`, `run_history`
- CRUD operations and analytics queries

**Entity Resolution** (`src/tradz/entity_resolver.py`):
- Resolves tickers/CIKs/names to unique Entity IDs
- Syncs reference data from SEC (`company_tickers.json`)
- Extracts entities from unstructured text (cashtags, names)

**Scoring** (`src/tradz/scoring.py`):
- 4-dimensional signal scoring (0-100 each):
  - `anomaly_score`: Price/volume/volatility Z-scores
  - `catalyst_score`: News, SEC filings, Polymarket events
  - `flow_score`: Congress trades, 13F filings
  - `confidence_score`: Data quality and source verification
- Composite `attention_score` for ranking

**Data Sources** (`src/tradz/sources/`):
- `equities.py` - US stocks via yfinance
- `crypto.py` - Cryptocurrency via ccxt (Binance default, fallback to Coinbase/Kraken)
- `congress.py` - Congressional trading disclosures
- `hedgefunds.py` - SEC 13F hedge fund filings
- `polymarket.py` - Prediction market data
- `news.py` - News aggregation (NewsAPI or Yahoo Finance fallback)
- `sec_filings.py` - SEC filings (10-K, 10-Q, 8-K)
- `brokers/ibkr.py` - Interactive Brokers integration (optional)

**Processing**:
- `aggregator.py` - Orchestrates all data sources, saves to `data/{date}.json`
- `signals.py` - Legacy signal generation (uses new Scorer internally)

**Reporting**:
- `report.py` - Template-based Markdown report generation
- `claude_reporter.py` - Claude Code CLI integration for AI-powered reports
- `reporting/fact_generator.py` - Generates deterministic FactTable for LLM
- `emailer.py` - SMTP email delivery with dry-run support

### Web Dashboard

The web dashboard provides a Robinhood-style clean interface for visualizing trading signals.

**API Backend** (`api/`):
- `main.py` - FastAPI application entry point
- `config.py` - API configuration (CORS, settings)
- `routers/` - Route handlers:
  - `signals.py` - GET/POST signals, refresh
  - `sources.py` - Data source status
  - `reports.py` - Report retrieval
- `services/` - Business logic:
  - `signal_service.py` - Signal operations
  - `aggregator_service.py` - Data aggregation
  - `cache_service.py` - In-memory caching
- `schemas/` - Pydantic request/response models

**Frontend** (`frontend/`):
- React + TypeScript + Vite
- Tailwind CSS for Robinhood-style clean design
- TanStack Query for data fetching with auto-refresh
- Responsive layout with collapsible sidebar
- Key files:
  - `src/App.tsx` - Root component with tab-based routing
  - `src/pages/Dashboard.tsx` - Signal heatmap and top signals overview
  - `src/pages/Sources.tsx` - Data source status panels
  - `src/pages/UsageGuide.tsx` - Interactive collapsible usage guide
  - `src/components/layout/Layout.tsx` - Main layout with header and sidebar
  - `src/components/signals/` - SignalCard, SignalHeatmap, TopSignals
  - `src/components/sources/` - CongressPanel, HedgeFundPanel, NewsPanel, PolymarketPanel
  - `src/hooks/useSignals.ts` - Data fetching hooks with 5-minute auto-refresh

### Configuration

**`config.yaml`**: Watchlists, thresholds, source toggles, Claude settings
- Enable/disable individual data sources via `enabled: true/false`
- Signal thresholds in `thresholds:` section
- Claude CLI settings in `claude:` section

**`.env`**: Sensitive credentials (SMTP, API keys)
- `DRY_RUN=1` prevents actual email sending
- Copy from `.env.example` and configure

**`api/config.py`**: API server settings
- CORS origins configuration
- API title, description, version

### Output Files

Reports are saved to `reports/` directory:
- `{date}.md` - Markdown report
- `{date}.json` - Raw signals data

Aggregated data saved to `data/` directory:
- `{date}.json` - All source data combined
- `tradz.duckdb` - DuckDB database with entities, observations, events, signals

## Key Patterns

- All data sources follow the same interface: `fetch_data()`, `get_latest_data()`, `close()`
- Retry logic with exponential backoff in data sources
- DataFrame-based data processing with pandas
- 4-dimensional signal scores (anomaly, catalyst, flow, confidence) with composite attention_score
- Entity resolution for cross-source data alignment
- DuckDB for persistent storage with singleton pattern
- API uses Pydantic schemas for request/response validation
- Frontend uses TanStack Query for server state management with 5-minute auto-refresh
- Robinhood-style clean UI with responsive layout and collapsible sidebar
- Tab-based navigation (Dashboard, Sources, Usage Guide)
- Services layer abstracts business logic from route handlers
- FactTable provides deterministic facts for LLM narrative generation
