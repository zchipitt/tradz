/**
 * Usage Guide page component.
 * User-focused guide explaining how to use the Tradz web application.
 * Brutalist design aesthetic - black/white + yellow accent.
 */
import { useState } from 'react';
import { 
    ChevronDown, 
    ChevronRight, 
    HelpCircle,
    LayoutDashboard,
    TrendingUp,
    Database,
    FileText,
    Settings,
    Target,
    Pin,
    Clock,
    CheckCircle,
    XCircle,
    AlertTriangle,
    Zap,
    BarChart3,
    Eye,
    Bell,
    CircleDot,
    MessageCircleQuestion
} from 'lucide-react';

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

function InfoBox({ type, children }: { type: 'tip' | 'note' | 'warning'; children: React.ReactNode }) {
    const styles = {
        tip: 'bg-green-50 border-green-600 text-green-800',
        note: 'bg-blue-50 border-blue-600 text-blue-800',
        warning: 'bg-yellow-50 border-yellow-600 text-yellow-800',
    };
    const icons = {
        tip: <Zap size={14} />,
        note: <Eye size={14} />,
        warning: <AlertTriangle size={14} />,
    };
    const labels = {
        tip: 'TIP',
        note: 'NOTE',
        warning: 'WARNING',
    };

    return (
        <div className={`border-l-4 p-3 mb-3 ${styles[type]}`}>
            <div className="flex items-center gap-2 font-bold text-xs mb-1">
                {icons[type]} {labels[type]}
            </div>
            <div className="text-sm">{children}</div>
        </div>
    );
}

function ScoreBadge({ label, color, description }: { label: string; color: string; description: string }) {
    return (
        <div className="flex items-center gap-3 p-2 bg-gray-50 border border-gray-200 mb-2">
            <div className={`w-8 h-8 ${color} flex items-center justify-center text-white text-xs font-bold`}>
                {label}
            </div>
            <span className="text-sm text-gray-700">{description}</span>
        </div>
    );
}

function StatusBadge({ status, description }: { status: string; description: string }) {
    const colors: Record<string, string> = {
        new: 'bg-green-500',
        ongoing: 'bg-blue-500',
        stale: 'bg-yellow-500',
        resolved: 'bg-gray-400',
        dismissed: 'bg-red-400',
    };
    return (
        <div className="flex items-center gap-3 p-2 bg-gray-50 border border-gray-200 mb-2">
            <div className={`px-2 py-1 ${colors[status]} text-white text-xs font-bold uppercase`}>
                {status}
            </div>
            <span className="text-sm text-gray-700">{description}</span>
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
                        <HelpCircle size={16} />
                        <span className="text-sm font-bold uppercase tracking-wider">
                            How to Use Tradz
                        </span>
                    </div>
                </div>
                <div className="p-4">
                    <h1 className="text-xl font-bold mb-2">Welcome to Tradz</h1>
                    <p className="text-gray-600 text-sm">
                        Your multi-source trading intelligence platform. This guide will help you understand 
                        how to use the dashboard effectively and make the most of the trading signals.
                    </p>
                </div>
            </div>

            {/* What is Tradz */}
            <Section title="What is Tradz?" icon={<Target size={16} />} defaultOpen={true}>
                <p className="mb-4 text-sm text-gray-700">
                    Tradz is a <strong>trading signal aggregation platform</strong> that collects data from multiple sources 
                    and presents actionable insights through an event-driven interface.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    What We Track
                </h4>
                <div className="grid grid-cols-2 gap-2 mb-4">
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">📈 US Equities</span>
                        <p className="text-xs text-gray-600 mt-1">Major stocks like AAPL, NVDA, TSLA</p>
                    </div>
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">💰 Crypto</span>
                        <p className="text-xs text-gray-600 mt-1">BTC, ETH, SOL and more</p>
                    </div>
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">🏛️ Congress Trades</span>
                        <p className="text-xs text-gray-600 mt-1">What politicians are buying/selling</p>
                    </div>
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">🏦 Hedge Fund 13F</span>
                        <p className="text-xs text-gray-600 mt-1">Institutional holdings changes</p>
                    </div>
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">🎰 Polymarket</span>
                        <p className="text-xs text-gray-600 mt-1">Prediction market odds</p>
                    </div>
                    <div className="p-2 bg-gray-50 border border-gray-200">
                        <span className="font-bold text-xs">📰 News</span>
                        <p className="text-xs text-gray-600 mt-1">Market-moving headlines</p>
                    </div>
                </div>

                <InfoBox type="tip">
                    Instead of checking multiple sources manually, Tradz aggregates everything into 
                    <strong> Events</strong> - actionable items ranked by importance.
                </InfoBox>
            </Section>

            {/* Understanding the Dashboard */}
            <Section title="Dashboard Overview" icon={<LayoutDashboard size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    The Dashboard is your main view. It shows the most important trading signals 
                    organized as <strong>Events</strong> - things worth your attention.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    Dashboard Components
                </h4>

                <div className="space-y-3 mb-4">
                    <div className="p-3 bg-gray-50 border-l-4 border-blue-500">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <Bell size={14} /> Signal Inbox
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Your main feed of events, sorted by <strong>Attention Score</strong>. 
                            The higher the score, the more important the event.
                        </p>
                    </div>

                    <div className="p-3 bg-gray-50 border-l-4 border-green-500">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <FileText size={14} /> Daily Brief
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            AI-generated summary of the day's key events and trade ideas. 
                            Great for a quick overview.
                        </p>
                    </div>

                    <div className="p-3 bg-gray-50 border-l-4 border-yellow-500">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <BarChart3 size={14} /> System Status
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Shows data freshness and source health. Green = good, Red = issues.
                        </p>
                    </div>

                    <div className="p-3 bg-gray-50 border-l-4 border-purple-500">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <CircleDot size={14} /> Open Loops
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Questions or research items that need follow-up. Track what you're investigating.
                        </p>
                    </div>
                </div>

                <InfoBox type="note">
                    Pinned events always appear at the top of your inbox. Use this for events you want to monitor closely.
                </InfoBox>
            </Section>

            {/* Understanding Events */}
            <Section title="Understanding Events" icon={<Zap size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    An <strong>Event</strong> is a significant market occurrence detected by our system. 
                    Each event card shows you everything you need to make a decision.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    The 4D Scoring System
                </h4>
                <p className="text-sm text-gray-700 mb-3">
                    Every event is scored across 4 dimensions (0-100 each):
                </p>

                <ScoreBadge 
                    label="A" 
                    color="bg-red-500" 
                    description="Anomaly — How unusual is the price/volume movement?"
                />
                <ScoreBadge 
                    label="C" 
                    color="bg-orange-500" 
                    description="Catalyst — Is there news, SEC filings, or prediction market activity?"
                />
                <ScoreBadge 
                    label="F" 
                    color="bg-blue-500" 
                    description="Flow — Are Congress members or hedge funds trading this?"
                />
                <ScoreBadge 
                    label="Cf" 
                    color="bg-green-500" 
                    description="Confidence — How reliable is the data? Multiple sources?"
                />

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    Attention Score
                </h4>
                <p className="text-sm text-gray-700 mb-3">
                    The big number on each event card. It combines all 4 scores to give you a single importance ranking.
                </p>
                <div className="grid grid-cols-2 gap-2 mb-4">
                    <div className="p-2 bg-red-100 border border-red-300 text-center">
                        <span className="font-bold text-lg">80-100</span>
                        <p className="text-xs text-red-700">Critical — Act Now</p>
                    </div>
                    <div className="p-2 bg-orange-100 border border-orange-300 text-center">
                        <span className="font-bold text-lg">65-79</span>
                        <p className="text-xs text-orange-700">Strong — Worth Attention</p>
                    </div>
                    <div className="p-2 bg-yellow-100 border border-yellow-300 text-center">
                        <span className="font-bold text-lg">50-64</span>
                        <p className="text-xs text-yellow-700">Moderate — Monitor</p>
                    </div>
                    <div className="p-2 bg-gray-100 border border-gray-300 text-center">
                        <span className="font-bold text-lg">0-49</span>
                        <p className="text-xs text-gray-600">Low — Background Noise</p>
                    </div>
                </div>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    Event Status
                </h4>
                <StatusBadge status="new" description="Just detected, first time seeing this" />
                <StatusBadge status="ongoing" description="Being tracked, may have updates" />
                <StatusBadge status="stale" description="No new data for 72+ hours" />
                <StatusBadge status="resolved" description="You marked this as handled" />
                <StatusBadge status="dismissed" description="You chose to ignore this" />

                <InfoBox type="tip">
                    Events automatically transition: <strong>new → ongoing</strong> after 1 hour, 
                    and <strong>ongoing → stale</strong> if no updates for 72 hours.
                </InfoBox>
            </Section>

            {/* Event Actions */}
            <Section title="Taking Action on Events" icon={<CheckCircle size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    Each event has actions you can take to manage your workflow:
                </p>

                <div className="space-y-3 mb-4">
                    <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200">
                        <Pin size={18} className="text-blue-500 mt-0.5" />
                        <div>
                            <div className="font-bold text-sm">Pin / Unpin</div>
                            <p className="text-xs text-gray-600">
                                Pin important events to keep them at the top of your inbox. 
                                Great for events you're actively monitoring.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200">
                        <Clock size={18} className="text-yellow-500 mt-0.5" />
                        <div>
                            <div className="font-bold text-sm">Snooze (24h)</div>
                            <p className="text-xs text-gray-600">
                                Hide an event for 24 hours. Useful when you want to revisit later 
                                but don't need to see it now.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200">
                        <CheckCircle size={18} className="text-green-500 mt-0.5" />
                        <div>
                            <div className="font-bold text-sm">Resolve</div>
                            <p className="text-xs text-gray-600">
                                Mark an event as handled. Use this when you've taken action 
                                or the event is no longer relevant.
                            </p>
                        </div>
                    </div>

                    <div className="flex items-start gap-3 p-3 bg-gray-50 border border-gray-200">
                        <XCircle size={18} className="text-red-500 mt-0.5" />
                        <div>
                            <div className="font-bold text-sm">Dismiss</div>
                            <p className="text-xs text-gray-600">
                                Remove from your inbox. Use this for false positives or events 
                                you don't care about.
                            </p>
                        </div>
                    </div>
                </div>

                <InfoBox type="note">
                    Click on any event card to see its <strong>Event Detail</strong> page with 
                    full evidence timeline and score breakdown.
                </InfoBox>
            </Section>

            {/* Quality Gates & Trade Ideas */}
            <Section title="Trade Ideas & Research Plans" icon={<Target size={16} />}>
                <p className="mb-4 text-sm text-gray-700">
                    High-quality events may include <strong>Trade Ideas</strong> with specific entry/exit levels. 
                    Events that don't meet quality standards get a <strong>Research Plan</strong> instead.
                </p>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    Trade Idea (High Confidence Events)
                </h4>
                <div className="p-3 bg-green-50 border border-green-200 mb-4">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                        <div><strong>Direction:</strong> Long / Short / Neutral</div>
                        <div><strong>Entry Zone:</strong> Suggested price range</div>
                        <div><strong>Target:</strong> Price target</div>
                        <div><strong>Stop Loss:</strong> Risk management level</div>
                    </div>
                    <p className="text-xs text-green-700 mt-2">
                        Also includes invalidation conditions and time horizon.
                    </p>
                </div>

                <h4 className="font-bold uppercase tracking-wide text-xs mt-4 mb-3 border-b border-black pb-1">
                    Research Plan (Needs More Data)
                </h4>
                <div className="p-3 bg-yellow-50 border border-yellow-200 mb-4">
                    <div className="text-xs space-y-1">
                        <div><strong>Questions to Verify:</strong> What you should research</div>
                        <div><strong>Evidence to Watch:</strong> What data to monitor</div>
                        <div><strong>Next Check:</strong> When to revisit</div>
                    </div>
                    <p className="text-xs text-yellow-700 mt-2">
                        These events need more confirmation before acting.
                    </p>
                </div>

                <InfoBox type="tip">
                    You can adjust quality thresholds in the <strong>Settings</strong> page 
                    to be more or less strict about what qualifies as a trade idea.
                </InfoBox>
            </Section>

            {/* Other Pages */}
            <Section title="Other Pages" icon={<LayoutDashboard size={16} />}>
                <div className="space-y-4">
                    <div className="p-3 border-l-4 border-black bg-gray-50">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <TrendingUp size={14} /> Signals Page
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Raw signal data in table format. Great for analysis and CSV export. 
                            Filter by asset type (equities, crypto) and sort by any column.
                        </p>
                    </div>

                    <div className="p-3 border-l-4 border-black bg-gray-50">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <Database size={14} /> Sources Page
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Detailed view of each data source. See Congress trades, hedge fund moves, 
                            news articles, and Polymarket predictions separately.
                        </p>
                    </div>

                    <div className="p-3 border-l-4 border-black bg-gray-50">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <FileText size={14} /> Reports Page
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Historical daily reports archive. Download past reports in Markdown 
                            or JSON format. Compare with previous days.
                        </p>
                    </div>

                    <div className="p-3 border-l-4 border-black bg-gray-50">
                        <div className="font-bold text-sm flex items-center gap-2">
                            <Settings size={14} /> Settings Page
                        </div>
                        <p className="text-xs text-gray-600 mt-1">
                            Configure quality gate thresholds. Adjust how strict the system is 
                            about generating trade ideas vs research plans.
                        </p>
                    </div>
                </div>
            </Section>

            {/* FAQ */}
            <Section title="Frequently Asked Questions" icon={<MessageCircleQuestion size={16} />}>
                <div className="space-y-4">
                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">How often is data updated?</h4>
                        <p className="text-xs text-gray-600">
                            Market data (stocks, crypto) updates every few minutes during market hours. 
                            Congress trades and 13F filings have regulatory delays (up to 45 days). 
                            News and Polymarket are near real-time.
                        </p>
                    </div>

                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">Why is an event showing "stale"?</h4>
                        <p className="text-xs text-gray-600">
                            Events become stale when there's no new data for 72+ hours. This usually means 
                            the situation has stabilized. You can resolve or dismiss stale events.
                        </p>
                    </div>

                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">What does a high Anomaly score mean?</h4>
                        <p className="text-xs text-gray-600">
                            High Anomaly (A) means unusual price or volume movement compared to historical norms. 
                            It doesn't mean good or bad — just that something abnormal is happening.
                        </p>
                    </div>

                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">Should I trust the trade ideas?</h4>
                        <p className="text-xs text-gray-600">
                            Trade ideas are <strong>suggestions based on data</strong>, not financial advice. 
                            Always do your own research. The system helps identify opportunities, 
                            but you make the final decision.
                        </p>
                    </div>

                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">How do I track something I want to research?</h4>
                        <p className="text-xs text-gray-600">
                            Use <strong>Open Loops</strong> to track questions or research items. 
                            You can link them to events and add progress notes as you investigate.
                        </p>
                    </div>

                    <div className="border-b border-gray-200 pb-3">
                        <h4 className="font-bold text-sm mb-1">Why don't I see trade ideas on all events?</h4>
                        <p className="text-xs text-gray-600">
                            Trade ideas only appear when an event passes all quality gates (minimum confidence, 
                            multiple sources, etc.). Events that don't meet these thresholds get a research plan instead.
                        </p>
                    </div>

                    <div className="pb-3">
                        <h4 className="font-bold text-sm mb-1">Can I customize which events I see?</h4>
                        <p className="text-xs text-gray-600">
                            Yes! Use the filter buttons (Active / Resolved / All) in the Signal Inbox. 
                            Pin important events, dismiss irrelevant ones, and adjust quality gate 
                            settings to change what qualifies as high-priority.
                        </p>
                    </div>
                </div>
            </Section>

            {/* Quick Tips */}
            <div className="bg-primary/20 border-2 border-black p-4 mb-4">
                <h3 className="font-bold uppercase tracking-wide text-sm mb-3 flex items-center gap-2">
                    <Zap size={16} /> Quick Tips
                </h3>
                <ul className="text-sm text-gray-700 space-y-2">
                    <li className="flex items-start gap-2">
                        <span className="font-bold">1.</span>
                        Start your day with the <strong>Daily Brief</strong> for a quick overview
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="font-bold">2.</span>
                        Focus on events with <strong>Attention Score 65+</strong> first
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="font-bold">3.</span>
                        <strong>Pin</strong> events you're actively monitoring
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="font-bold">4.</span>
                        Check the <strong>Flow (F)</strong> score for insider activity signals
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="font-bold">5.</span>
                        Use <strong>Open Loops</strong> to track your research questions
                    </li>
                </ul>
            </div>

            <div className="mt-4 text-center text-xs text-gray-500">
                Need help? Check the detailed documentation or contact support.
            </div>
        </div>
    );
}
