/**
 * Main layout component with brutalist design aesthetic.
 * Black/white + yellow accent, dot grid background, hard borders.
 */
import { useState } from 'react';
import {
  RefreshCw,
  Menu,
  X,
  Zap,
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
    { id: 'today' as const, label: 'Today', description: 'Event inbox & daily brief' },
    { id: 'signals' as const, label: 'Signals', description: 'Raw signals data' },
    { id: 'sources' as const, label: 'Sources', description: 'Data source status' },
    { id: 'reports' as const, label: 'Reports', description: 'Historical briefs' },
    { id: 'guide' as const, label: 'Docs', description: 'Usage guide' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header - Brutalist white navbar with black border */}
      <header className="fixed top-0 left-0 right-0 z-50 h-14 bg-white border-b-2 border-black">
        <div className="flex items-center justify-between px-6 h-full max-w-7xl mx-auto">
          {/* Left: Mobile menu + Logo */}
          <div className="flex items-center gap-6">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 text-black hover:bg-gray-100 transition-colors cursor-pointer border border-black"
            >
              {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
            </button>

            {/* Logo - Left aligned */}
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-black" strokeWidth={2.5} />
              <span className="text-lg font-bold text-black tracking-tight">
                Tradz
              </span>
              <span className="hidden sm:inline text-sm text-gray-500 font-normal ml-2">
                - Signal Aggregator
              </span>
            </div>
          </div>

          {/* Center: Desktop Navigation */}
          <nav className="hidden lg:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    'px-4 py-1.5 text-sm transition-all duration-100 cursor-pointer',
                    isActive
                      ? 'font-bold underline underline-offset-4 text-black'
                      : 'text-gray-600 hover:text-black hover:underline hover:underline-offset-4'
                  )}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right: Status + Actions */}
          <div className="flex items-center gap-4">
            {/* Last Updated - Status capsule */}
            {lastUpdated && (
              <div className="hidden sm:flex items-center gap-2 px-3 py-1 border border-gray-300 bg-gray-50 text-xs">
                <span className="text-gray-500">Last sync:</span>
                <span className="text-black">{lastUpdated}</span>
              </div>
            )}

            {/* Refresh Button - Yellow CTA */}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={cn(
                  'flex items-center gap-2 px-4 py-1.5 text-sm font-bold uppercase tracking-wider',
                  'bg-primary border-2 border-black text-black',
                  'hover:shadow-brutal-sm transition-all duration-100 cursor-pointer',
                  'disabled:opacity-50 disabled:cursor-not-allowed'
                )}

              >
                <RefreshCw
                  size={14}
                  className={cn(isRefreshing && 'animate-spin')}
                />
                <span>Scan</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1 pt-14">
        {/* Sidebar - Mobile only */}
        <aside
          className={cn(
            'fixed lg:hidden top-14 left-0 z-40 h-[calc(100vh-3.5rem)]',
            'w-64 bg-white border-r-2 border-black',
            'transform transition-transform duration-200 ease-out',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full'
          )}
        >
          {/* Sidebar Header */}
          <div className="px-4 py-3 border-b-2 border-black bg-gray-100">
            <span className="text-sm font-bold uppercase tracking-wider">
              Navigation
            </span>
          </div>

          <nav className="p-4 space-y-2">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onTabChange(item.id);
                    setSidebarOpen(false);
                  }}
                  className={cn(
                    'w-full text-left px-4 py-3 text-sm',
                    'border-2 transition-all duration-100 cursor-pointer',
                    isActive
                      ? 'bg-primary border-black font-bold'
                      : 'bg-white border-gray-300 hover:border-black hover:bg-gray-50'
                  )}
                >
                  <div className="font-bold uppercase tracking-wider">{item.label}</div>
                  <div className="text-xs text-gray-500 mt-0.5 normal-case font-normal">
                    {item.description}
                  </div>
                </button>
              );
            })}
          </nav>

          {/* Sidebar Footer */}
          <div className="absolute bottom-0 left-0 right-0 p-4 border-t-2 border-black bg-gray-100">
            <div className="text-xs text-gray-600">
              <p className="font-bold">TRADZ v2.0</p>
              <p className="mt-1">Event-centric signal aggregation</p>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/40 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content - Dot grid background */}
        <main className="flex-1 overflow-auto bg-dot-grid min-h-[calc(100vh-3.5rem)]">
          <div className="max-w-7xl mx-auto p-6 lg:p-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
