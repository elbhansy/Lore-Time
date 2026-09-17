import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ApplicationShell } from './components/layout/ApplicationShell';
import { TemporalProvider, useTemporalContext } from './state/temporal/temporal-context';
import { ShellProvider } from './state/shell/shell-context';
import { GlobalErrorBoundary } from './components/feedback/GlobalErrorBoundary';
import { OverviewPage } from './pages/overview/OverviewPage';
import { TimelinePage } from './pages/timeline/TimelinePage';
import { CharactersPage } from './pages/characters/CharactersPage';
import { CharacterProfilePage } from './pages/characters/CharacterProfilePage';
import { GraphPage } from './pages/graph/GraphPage';
import { CausalityPage } from './pages/causality/CausalityPage';
import { NarrativePage } from './pages/narrative/NarrativePage';
import { WhatIfPage } from './pages/whatIf/WhatIfPage';
import { SeriesPage } from './pages/SeriesPage';
import { FactionProfile } from './features/factions/components/FactionProfile';
import { PageLayout } from './components/layout/PageLayout';
import { EmptyState } from './components/feedback/EmptyState';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

const DEFAULT_SERIES_ID =
  import.meta.env.VITE_DEFAULT_SERIES_ID ?? 'a9d1b78b-dcb4-46f7-b0d2-8a8dcf96e177';

const SeriesContainer: React.FC<{ children?: React.ReactNode }> = ({ children }) => {
  const { seriesId = DEFAULT_SERIES_ID } = useParams<{ seriesId: string }>();

  return (
    <TemporalProvider seriesId={seriesId}>
      <ShellProvider>
        <ApplicationShell seriesId={seriesId}>
          {children}
        </ApplicationShell>
      </ShellProvider>
    </TemporalProvider>
  );
};

const PlaceholderView: React.FC<{ name: string }> = ({ name }) => {
  const { readerChapter } = useTemporalContext();
  return (
    <PageLayout title={name} subtitle={`Investigation view configured for Chapter ${readerChapter}`}>
      <EmptyState
        title={`${name} Under Architecture`}
        description={`The foundation for this intelligence view is established. Implementation connects in upcoming phases.`}
      />
    </PageLayout>
  );
};

function App() {
  return (
    <GlobalErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Navigate to={`/series/${DEFAULT_SERIES_ID}`} replace />} />

            {/* Architecture Routes with ApplicationShell and Temporal Context */}
            <Route
              path="/series/:seriesId"
              element={
                <SeriesContainer>
                  <OverviewPage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/legacy"
              element={
                <SeriesContainer>
                  <SeriesPage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/timeline"
              element={
                <SeriesContainer>
                  <TimelinePage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/characters"
              element={
                <SeriesContainer>
                  <CharactersPage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/characters/:characterId"
              element={
                <SeriesContainer>
                  <CharacterProfilePage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/factions/:factionId"
              element={
                <SeriesContainer>
                  <FactionProfile />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/graph"
              element={
                <SeriesContainer>
                  <GraphPage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/causality"
              element={
                <SeriesContainer>
                  <CausalityPage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/narrative"
              element={
                <SeriesContainer>
                  <NarrativePage />
                </SeriesContainer>
              }
            />

            <Route
              path="/series/:seriesId/what-if"
              element={
                <SeriesContainer>
                  <WhatIfPage />
                </SeriesContainer>
              }
            />

            {/* 404 Route */}
            <Route
              path="*"
              element={
                <div style={{ padding: '48px', textAlign: 'center' }}>
                  <EmptyState
                    title="404 — Route Not Found"
                    description="The requested story intelligence route does not exist."
                  />
                </div>
              }
            />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </GlobalErrorBoundary>
  );
}

export default App;
