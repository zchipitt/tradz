/**
 * Main layout component with header and sidebar.
 * Robinhood-style clean light theme.
 */
import { useState } from 'react';
import {
  LayoutDashboard,
  TrendingUp,
  Newspaper,
  RefreshCw,
  Menu,
  X,
  BookOpen,
  BarChart3,
  FileText,
} from 'lucide-react';
import { cn } from '../../lib/utils';

export type TabId = 'today' | 'signals' | 'sources' | 'reports' | 'guide';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  lastUpdated?: string;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

export function Layout({
  children,
  activeTab,
  onTabChange,
  lastUpdated,
  onRefresh,
  isRefreshing,
}: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const navItems = [
    { id: 'today' as const, label: 'Today', icon: LayoutDashboard, description: 'Event inbox & daily brief' },
    { id: 'signals' as const, label: 'Signals', icon: BarChart3, description: 'Raw signals data' },
    { id: 'sources' as const, label: 'Sources', icon: Newspaper, description: 'Data source status' },
    { id: 'reports' as const, label: 'Reports', icon: FileText, description: 'Historical briefs' },
    { id: 'guide' as const, label: 'Guide', icon: BookOpen, description: 'Usage guide' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-background text-text">
      {/* Header - Clean white Robinhood style */}
      <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-white border-b border-border shadow-sm">
        <div className="flex items-center justify-between px-4 h-full max-w-7xl mx-auto w-full">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors cursor-pointer"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-primary" />
              <span className="font-bold text-xl tracking-tight text-text">Tradz</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-sm text-text-muted hidden sm:block">
                Updated: {lastUpdated}
              </span>
            )}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={cn(
                  'flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium',
                  'bg-primary text-white hover:bg-primary-dark',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-all duration-200 cursor-pointer'
                )}
              >
                <RefreshCw
                  size={14}
                  className={cn(isRefreshing && 'animate-spin')}
                />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-16 max-w-7xl mx-auto w-full">
        {/* Sidebar - Clean white */}
        <aside
          className={cn(
            'fixed lg:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)]',
            'w-56 bg-white border-r border-border',
            'transform transition-transform duration-300 ease-out',
            'lg:transform-none lg:block',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          )}
        >
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onTabChange(item.id);
                    setSidebarOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium',
                    'transition-all duration-150 cursor-pointer',
                    isActive
                      ? 'bg-primary-light text-primary font-semibold'
                      : 'text-text-muted hover:text-text hover:bg-surface'
                  )}
                >
                  <Icon size={18} className={cn(isActive ? 'text-primary' : 'text-text-muted')} />
                  <div className="text-left">
                    <div>{item.label}</div>
                    {isActive && (
                      <div className="text-xs font-normal opacity-70">{item.description}</div>
                    )}
                  </div>
                </button>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border">
            <div className="text-xs text-text-muted">
              <p className="font-medium">Tradz v2.0</p>
              <p className="mt-1">Event-centric signals</p>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/20 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 p-4 lg:p-8 overflow-auto bg-background">
          {children}
        </main>
      </div>
    </div>
  );
}
