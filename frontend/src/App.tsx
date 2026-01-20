/**
 * Root application component.
 * Event-centric trading signal dashboard.
 */
import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout, type TabId } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Signals } from './pages/Signals';
import { Sources } from './pages/Sources';
import { Reports } from './pages/Reports';
import { UsageGuide } from './pages/UsageGuide';
import { useEvents, useRefreshEvents } from './hooks/useEvents';
import { useRefreshSignals } from './hooks/useSignals';
import { formatDate } from './lib/utils';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppContent() {
  const [activeTab, setActiveTab] = useState<TabId>('today');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { data: eventsData } = useEvents();
  const refreshEvents = useRefreshEvents();
  const refreshSignals = useRefreshSignals();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([refreshEvents(), refreshSignals()]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const lastUpdated = eventsData?.generated_at ? formatDate(eventsData.generated_at) : undefined;

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      lastUpdated={lastUpdated}
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
    >
      {activeTab === 'today' && (
        <Dashboard
          onRefresh={handleRefresh}
          isRefreshing={isRefreshing}
        />
      )}
      {activeTab === 'signals' && <Signals />}
      {activeTab === 'sources' && <Sources />}
      {activeTab === 'reports' && <Reports />}
      {activeTab === 'guide' && <UsageGuide />}
    </Layout>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}
