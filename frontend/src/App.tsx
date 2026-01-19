/**
 * Root application component.
 */
import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Sources } from './pages/Sources';
import { useSignals, useRefreshSignals } from './hooks/useSignals';
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
  const [activeTab, setActiveTab] = useState<'dashboard' | 'sources'>('dashboard');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const { data } = useSignals();
  const refreshSignals = useRefreshSignals();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refreshSignals();
    } finally {
      setIsRefreshing(false);
    }
  };

  const lastUpdated = data?.generated_at ? formatDate(data.generated_at) : undefined;

  return (
    <Layout
      activeTab={activeTab}
      onTabChange={setActiveTab}
      lastUpdated={lastUpdated}
      onRefresh={handleRefresh}
      isRefreshing={isRefreshing}
    >
      {activeTab === 'dashboard' && <Dashboard />}
      {activeTab === 'sources' && <Sources />}
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
