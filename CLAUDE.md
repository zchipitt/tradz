# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tradz is a daily trading signal aggregation system that collects data from multiple sources, generates quantitative signals, and delivers reports via email. It supports both template-based and Claude Code CLI-powered report generation.

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
```

## Architecture

### Data Flow
```
DataAggregator → SignalGenerator → ReportGenerator/ClaudeReporter → EmailSender
```

### Core Components

**Entry Point**: `src/tradz/run_nightly.py`
- Orchestrates the full pipeline: load config → aggregate data → generate signals → create report → send email

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
- `signals.py` - Calculates signal scores (0-100) based on price movement, volatility, volume

**Output**:
- `report.py` - Template-based Markdown report generation
- `claude_reporter.py` - Claude Code CLI integration for AI-powered reports
- `emailer.py` - SMTP email delivery with dry-run support

### Configuration

**`config.yaml`**: Watchlists, thresholds, source toggles, Claude settings
- Enable/disable individual data sources via `enabled: true/false`
- Signal thresholds in `thresholds:` section
- Claude CLI settings in `claude:` section

**`.env`**: Sensitive credentials (SMTP, API keys)
- `DRY_RUN=1` prevents actual email sending
- Copy from `.env.example` and configure

### Output Files

Reports are saved to `reports/` directory:
- `{date}.md` - Markdown report
- `{date}.json` - Raw signals data

Aggregated data saved to `data/` directory:
- `{date}.json` - All source data combined

## Key Patterns

- All data sources follow the same interface: `fetch_data()`, `get_latest_data()`, `close()`
- Retry logic with exponential backoff in data sources
- DataFrame-based data processing with pandas
- Signal scores calculated from momentum, volatility, and volume metrics
