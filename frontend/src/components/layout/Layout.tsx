/**
 * Main layout component with header and sidebar.
 */
import { useState } from 'react';
import { BarChart3, TrendingUp, Newspaper, RefreshCw, Menu, X } from 'lucide-react';
import { cn } from '../../lib/utils';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: 'dashboard' | 'sources';
  onTabChange: (tab: 'dashboard' | 'sources') => void;
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
    { id: 'dashboard' as const, label: 'Dashboard', icon: BarChart3 },
    { id: 'sources' as const, label: 'Sources', icon: Newspaper },
  ];

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100"
            >
              {sidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-blue-600" />
              <span className="font-bold text-xl">Tradz</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {lastUpdated && (
              <span className="text-sm text-gray-500 hidden sm:block">
                Updated: {lastUpdated}
              </span>
            )}
            {onRefresh && (
              <button
                onClick={onRefresh}
                disabled={isRefreshing}
                className={cn(
                  'flex items-center gap-2 px-3 py-2 rounded-lg',
                  'bg-blue-600 text-white hover:bg-blue-700',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors'
                )}
              >
                <RefreshCw
                  size={16}
                  className={cn(isRefreshing && 'animate-spin')}
                />
                <span className="hidden sm:inline">Refresh</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <div className="flex flex-1">
        {/* Sidebar */}
        <aside
          className={cn(
            'fixed lg:static inset-y-0 left-0 z-40',
            'w-64 bg-white border-r border-gray-200',
            'transform transition-transform duration-200 ease-in-out',
            'lg:transform-none pt-16 lg:pt-0',
            sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
          )}
        >
          <nav className="p-4 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onTabChange(item.id);
                    setSidebarOpen(false);
                  }}
                  className={cn(
                    'w-full flex items-center gap-3 px-3 py-2 rounded-lg',
                    'transition-colors text-left',
                    activeTab === item.id
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-700 hover:bg-gray-100'
                  )}
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Overlay for mobile sidebar */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/20 z-30 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 p-4 lg:p-6 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  );
}
