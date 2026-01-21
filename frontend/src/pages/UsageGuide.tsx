/**
 * Usage Guide page component.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { ChevronDown, ChevronRight, BookOpen, Settings, Play, BarChart3, Clock, AlertTriangle, Zap, Bot, Monitor, Database } from 'lucide-react';

interface SectionProps {
    title: string;
    icon: React.ReactNode;
    children: React.ReactNode;
    defaultOpen?: boolean;
}

function Section({ title, icon, children, defaultOpen = false }: SectionProps) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="bg-white border-2 border-black overflow-hidden mb-4 font-mono">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full flex items-center gap-3 px-4 py-3 bg-gray-100 hover:bg-gray-200 transition-colors text-left cursor-pointer border-b-2 border-black"
            >
                {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} className="text-gray-500" />}
                <span>{icon}</span>
                <span className="font-bold uppercase tracking-wide text-sm">{title}</span>
            </button>
            {isOpen && (
                <div className="p-4">
                    {children}
                </div>
            )}
        </div>
    );
}

function CodeBlock({ children }: { children: string }) {
    return (
        <pre className="bg-gray-100 border-2 border-black p-4 overflow-x-auto text-xs">
            <code>{children}</code>
        </pre>
    );
}

function Table({ headers, rows }: { headers: string[]; rows: string[][] }) {
    return (
        <div className="overflow-x-auto">
            <table className="min-w-full text-xs border-2 border-black">
                <thead>
                    <tr className="border-b-2 border-black bg-gray-100">
                        {headers.map((h, i) => (
                            <th key={i} className="px-3 py-2 text-left font-bold uppercase tracking-wide">{h}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {rows.map((row, i) => (
                        <tr key={i} className="border-b border-gray-200 hover:bg-gray-50">
                            {row.map((cell, j) => (
                                <td key={j} className="px-3 py-2 text-gray-700">{cell}</td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

export function UsageGuide() {
    return (
        <div className="max-w-4xl mx-auto font-mono">
            {/* Header */}
            <div className="bg-white border-2 border-black overflow-hidden mb-6">
                <div className="px-4 py-3 bg-gray-100 border-b-2 border-black flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <BookOpen size={16} />
                        <span className="text-sm font-bold uppercase tracking-wider">
                            Usage Guide
                        </span>
                    </div>
                </div>
                <div className="p-4">
                    <h1 className="text-xl font-bold mb-2">Tradz Documentation</h1>
                    <p className="text-gray-600 text-sm">Multi-source trading signal aggregation system</p>
                </div>
            </div>

            <Section title="1. System Overview" icon={<BookOpen size={16} />} defaultOpen={true}>
                <p className="mb-4 text-sm text-gray-700">
                    Tradz is a multi-source data aggregation system for automated trading signals, using 4D scoring and Claude AI for professional analysis reports.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Core Data Sources</h4>
                <Table
                    headers={['Module', 'Description', 'Latency']}
                    rows={[
                        ['EQUITIES', 'US stocks via yfinance', '15-20min'],
                        ['CRYPTO', 'Cryptocurrencies via ccxt', 'REALTIME'],
                        ['CONGRESS', 'Capitol Trades + Quiver/Finnhub', '~45d'],
                        ['13F FILINGS', 'SEC EDGAR institutional holdings', 'QUARTERLY'],
                        ['POLYMARKET', 'Prediction market odds', 'REALTIME'],
                        ['NEWS', 'Yahoo Finance + NewsAPI', 'REALTIME'],
                        ['SEC FILINGS', '10-K, 10-Q, 8-K documents', 'REALTIME'],
                    ]}
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">4D Signal Scoring</h4>
                <Table
                    headers={['Dimension', 'Description', 'Data Source']}
                    rows={[
                        ['ANOMALY', 'Price/volume/volatility Z-scores', 'MARKET DATA'],
                        ['CATALYST', 'News, SEC filings, Polymarket events', 'MULTI SOURCE'],
                        ['FLOW', 'Congress trades, 13F institutional flow', 'DISCLOSURE DATA'],
                        ['CONFIDENCE', 'Data quality and cross-source validation', 'QUALITY METRICS'],
                    ]}
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Web Dashboard</h4>
                <Table
                    headers={['Module', 'Description']}
                    rows={[
                        ['EVENT DASHBOARD', 'Event-centric design (from Ticker view)'],
                        ['SIGNAL INBOX', 'Event cards with 4D scores and evidence'],
                        ['STATE MACHINE', 'New/Ongoing/Stale/Resolved/Dismissed'],
                        ['EVENT ACTIONS', 'Pin/Snooze/Resolve/Dismiss'],
                        ['FASTAPI BACKEND', 'REST API for signals, sources, reports'],
                        ['AUTO REFRESH', 'TanStack Query with 5min intervals'],
                    ]}
                />
            </Section>

            <Section title="2. Installation" icon={<Settings size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Requirements</h4>
                <ul className="list-none mb-4 text-sm text-gray-700 space-y-1">
                    <li><span className="font-bold">+</span> Python: 3.8+</li>
                    <li><span className="font-bold">+</span> Node.js: 18+ (frontend + Claude CLI)</li>
                    <li><span className="font-bold">+</span> OS: macOS / Linux / Windows</li>
                </ul>

                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Setup Commands</h4>
                <CodeBlock>{`# Navigate to project
cd /path/to/tradz

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
vim .env`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Verify Installation</h4>
                <CodeBlock>{`source .venv/bin/activate
python3 -c "import yfinance; import ccxt; import duckdb; print('[OK] Dependencies installed')"

# Verify database
python3 scripts/verify_db.py`}</CodeBlock>
            </Section>

            <Section title="3. Configuration" icon={<Settings size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Environment Variables</h4>
                <Table
                    headers={['Variable', 'Description', 'Example']}
                    rows={[
                        ['DRY_RUN', 'Simulation mode (1=no email)', '1'],
                        ['SMTP_HOST', 'Mail server address', 'smtp.gmail.com'],
                        ['SMTP_PORT', 'Mail server port', '587'],
                        ['SMTP_USER', 'Email username', 'your@gmail.com'],
                        ['SMTP_PASS', 'App-specific password', 'xxxx-xxxx-xxxx'],
                        ['ANTHROPIC_API_KEY', 'Claude API key', 'sk-ant-api03-...'],
                    ]}
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Watchlist Config</h4>
                <CodeBlock>{`equities:
  tickers:
    - AAPL    # Apple
    - MSFT    # Microsoft
    - NVDA    # Nvidia

crypto:
  exchange: "binance"
  pairs:
    - BTC/USDT
    - ETH/USDT`}</CodeBlock>
            </Section>

            <Section title="4. Running System" icon={<Play size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">CLI Options</h4>
                <CodeBlock>{`python3 -m src.tradz.run_nightly [OPTIONS]

# Options:
#   --use-claude      Force Claude report generation
#   --template-only   Force template-based generation
#   --skip-email      Skip email delivery`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">One-Click Start</h4>
                <CodeBlock>{`# Start environment (backend 8002 + frontend 5173)
./scripts/local_up.sh

# Stop environment
./scripts/local_down.sh`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">View Reports</h4>
                <CodeBlock>{`# View today's report
cat reports/$(date +%Y-%m-%d).md

# View JSON data
cat reports/$(date +%Y-%m-%d).json`}</CodeBlock>
            </Section>

            <Section title="5. Signal Interpretation" icon={<BarChart3 size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">4D Scoring System</h4>
                <p className="mb-4 text-sm text-gray-700">Each signal is scored across 4 dimensions (0-100 each)</p>

                <Table
                    headers={['Dimension', 'Description', 'Weight']}
                    rows={[
                        ['ANOMALY', 'Price/volume/volatility statistical deviation', '30%'],
                        ['CATALYST', 'News, SEC filings, prediction market events', '30%'],
                        ['FLOW', 'Congress trades, 13F institutional flow', '25%'],
                        ['CONFIDENCE', 'Data quality and multi-source validation', '15%'],
                    ]}
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Attention Score Formula</h4>
                <CodeBlock>{`attention_score = anomaly × 0.30 + catalyst × 0.30 + flow × 0.25 + confidence × 0.15`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Signal Strength</h4>
                <Table
                    headers={['Range', 'Strength', 'Recommended Action']}
                    rows={[
                        ['80-100', 'CRITICAL', 'High priority - potential major event'],
                        ['65-79', 'STRONG', 'Worth attention'],
                        ['50-64', 'MODERATE', 'Monitor'],
                        ['0-49', 'WEAK', 'Normal fluctuation, no action'],
                    ]}
                />
            </Section>

            <Section title="6. Scheduled Tasks" icon={<Clock size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">macOS launchd</h4>
                <CodeBlock>{`# Load scheduled task
launchctl load ~/Library/LaunchAgents/com.tradz.nightly.plist

# Verify loaded
launchctl list | grep tradz

# Unload scheduled task
launchctl unload ~/Library/LaunchAgents/com.tradz.nightly.plist`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Linux Cron</h4>
                <CodeBlock>{`# Edit crontab
crontab -e

# Run daily at 06:30
30 6 * * * /path/to/tradz/scripts/nightly.sh >> /path/to/tradz/logs/cron.log 2>&1`}</CodeBlock>
            </Section>

            <Section title="7. Troubleshooting" icon={<AlertTriangle size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Common Errors</h4>

                <div className="bg-status-error/10 border-2 border-status-error p-3 mb-3">
                    <p className="font-bold text-status-error text-xs">[ERROR] ModuleNotFoundError: No module named 'yfinance'</p>
                    <p className="text-gray-600 text-xs mt-1">FIX: Activate venv and install dependencies</p>
                    <CodeBlock>{`source .venv/bin/activate
pip install -r requirements.txt`}</CodeBlock>
                </div>

                <div className="bg-status-warning/10 border-2 border-status-warning p-3 mb-3">
                    <p className="font-bold text-status-warning text-xs">[WARN] SMTP authentication failed</p>
                    <p className="text-gray-600 text-xs mt-1">FIX: Use app-specific password, not account password</p>
                </div>

                <div className="bg-status-warning/10 border-2 border-status-warning p-3 mb-3">
                    <p className="font-bold text-status-warning text-xs">[WARN] Claude CLI not found</p>
                    <CodeBlock>{`npm install -g @anthropic-ai/claude-code
claude --version`}</CodeBlock>
                </div>

                <div className="bg-status-info/10 border-2 border-status-info p-3">
                    <p className="font-bold text-status-info text-xs">[INFO] Congress trading data shows 0 records</p>
                    <p className="text-gray-600 text-xs mt-1">
                        System uses multi-source fallback: Capitol Trades - Quiver - Finnhub.
                        Configure QUIVER_API_KEY or FINNHUB_API_KEY in .env as backup sources.
                    </p>
                </div>
            </Section>

            <Section title="8. Advanced Usage" icon={<Zap size={16} />}>
                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Add More Tickers</h4>
                <CodeBlock>{`# Edit config.yaml
equities:
  tickers:
    - AAPL
    - YOUR_NEW_TICKER`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Adjust Thresholds</h4>
                <CodeBlock>{`thresholds:
  day_return_high: 7.0      # Increase for fewer, stronger signals
  volume_high: 3.0          # Increase for more extreme volume alerts`}</CodeBlock>
            </Section>

            <Section title="9. Claude AI Reports" icon={<Bot size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    Claude Code CLI uses MCP Skills to enhance report quality:
                </p>
                <ul className="list-none mb-4 text-sm text-gray-700 space-y-1">
                    <li><span className="font-bold text-status-info">+</span> <strong>tavily-search</strong>: Search latest news for each signal</li>
                    <li><span className="font-bold text-status-info">+</span> <strong>filesystem</strong>: Read historical reports for comparison</li>
                    <li><span className="font-bold text-status-info">+</span> <strong>sequential-thinking</strong>: Deep analysis for complex signals</li>
                    <li><span className="font-bold text-status-info">+</span> <strong>fetch</strong>: Retrieve webpage content</li>
                </ul>

                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Install Claude CLI</h4>
                <CodeBlock>{`npm install -g @anthropic-ai/claude-code

# Set API key in .env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Verify installation
claude --version`}</CodeBlock>
            </Section>

            <Section title="10. Web Dashboard" icon={<Monitor size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    Tradz provides an event-centric web dashboard, transformed from traditional Ticker view to event-driven design.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">One-Click Start</h4>
                <CodeBlock>{`# Start backend (8002) + frontend (5173)
./scripts/local_up.sh

# Stop all services
./scripts/local_down.sh`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Manual Start</h4>
                <CodeBlock>{`# Terminal 1: Start backend
uvicorn api.main:app --reload --port 8002

# Terminal 2: Start frontend
cd frontend && npm run dev`}</CodeBlock>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Access URLs</h4>
                <ul className="list-none text-sm text-gray-700 space-y-1">
                    <li><span className="font-bold">+</span> Frontend: <span className="font-bold">http://localhost:5173</span></li>
                    <li><span className="font-bold">+</span> API Docs: <span className="font-bold">http://localhost:8002/api/docs</span></li>
                </ul>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Event State Machine</h4>
                <Table
                    headers={['State', 'Description', 'Color']}
                    rows={[
                        ['new', 'New event, first appearance', 'GREEN'],
                        ['ongoing', 'In progress, being tracked', 'BLUE'],
                        ['stale', 'Expired, no updates for 72h+', 'YELLOW'],
                        ['resolved', 'Resolved, user marked complete', 'GRAY'],
                        ['dismissed', 'Dismissed, user chose to ignore', 'RED'],
                    ]}
                />
            </Section>

            <Section title="11. Database & Entity Resolution" icon={<Database size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    Tradz uses DuckDB as local analytics database, stored at <code className="bg-gray-100 px-1.5 py-0.5 border border-black">data/tradz.duckdb</code>.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mb-2 border-b border-black pb-1">Database Tables</h4>
                <Table
                    headers={['Table', 'Description']}
                    rows={[
                        ['entities', 'Entity table (Ticker/CIK/company name mappings)'],
                        ['observations', 'Observations table (raw data points from sources)'],
                        ['events', 'Events table (aggregated stories linking observations)'],
                        ['signals', 'Signals table (daily 4D scored output)'],
                        ['run_history', 'Run history (for observability)'],
                    ]}
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-2 border-b border-black pb-1">Verification Scripts</h4>
                <CodeBlock>{`# Verify database schema
python3 scripts/verify_db.py

# Verify entity resolution
python3 scripts/verify_entities.py

# Verify signal generation
python3 scripts/verify_signals.py

# Verify fact generation
python3 scripts/verify_facts.py`}</CodeBlock>
            </Section>

            <div className="mt-6 p-4 bg-primary/20 border-2 border-black">
                <p className="text-xs">
                    <span className="font-bold">TIP:</span> For complete documentation, see <code className="bg-white px-1.5 py-0.5 border border-black">docs/USAGE_GUIDE_CN.md</code>
                </p>
            </div>

            <div className="mt-4 text-center text-xs text-gray-500">
                Documentation version: 2026-01-20
            </div>
        </div>
    );
}
