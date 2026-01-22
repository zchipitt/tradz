/**
 * Root application component.
 * Event-centric trading signal dashboard with URL-based routing.
 */
import { useState } from 'react';
import { BrowserRouter, Routes, Route, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Layout, type TabId } from './components/layout/Layout';
import { Dashboard } from './pages/Dashboard';
import { Signals } from './pages/Signals';
import { Sources } from './pages/Sources';
import { Reports } from './pages/Reports';
import { UsageGuide } from './pages/UsageGuide';
import { EventDetail } from './pages/EventDetail';
import { useEvents, useRefreshEvents } from './hooks/useEvents';
import { useRefreshSignals } from './hooks/useSignals';
import { formatDate } from './lib/utils';
import type { Event } from './api/types';

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
  const navigate = useNavigate();

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([refreshEvents(), refreshSignals()]);
    } finally {
      setIsRefreshing(false);
    }
  };

  // Navigate to event detail page
  const handleEventOpen = (event: Event) => {
    navigate(`/events/${event.id}`);
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
          onEventOpen={handleEventOpen}
        />
      )}
      {activeTab === 'signals' && <Signals />}
      {activeTab === 'sources' && <Sources />}
      {activeTab === 'reports' && <Reports />}
      {activeTab === 'guide' && <UsageGuide />}
    </Layout>
  );
}

/**
 * Event Detail page wrapper - renders outside the main layout.
 */
function EventDetailPage() {
  return (
    <div className="min-h-screen bg-white bg-dot-grid">
      <EventDetail />
    </div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppContent />} />
          <Route path="/events/:eventId" element={<EventDetailPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
