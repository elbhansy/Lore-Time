import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider, useShellContext } from '../../../state/shell/shell-context';
import { GraphPage } from '../GraphPage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import { GenericGraphReadModel } from '../../../api/contracts/read-models';

// Mock ResizeObserver for xyflow/react
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserverMock as any;

const mockGraphCh10: GenericGraphReadModel = {
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  nodes: [
    { id: 'char-lyra', node_type: 'CHARACTER', label: 'Lyra', chapter: 1, metadata: {} },
    { id: 'char-kael', node_type: 'CHARACTER', label: 'Kael', chapter: 3, metadata: {} },
    { id: 'char-vane', node_type: 'CHARACTER', label: 'Lord Vane', chapter: 7, metadata: {} },
  ],
  edges: [
    {
      edge_id: 'rel:lyra:kael',
      source_id: 'char-lyra',
      target_id: 'char-kael',
      edge_type: 'RELATIONSHIP',
      label: 'ALLIED',
      chapter: 3,
      weight: 1.0,
      evidence_summary: 'Allied in chapter 3',
      metadata: {},
    },
    {
      edge_id: 'rel:vane:kael',
      source_id: 'char-vane',
      target_id: 'char-kael',
      edge_type: 'RELATIONSHIP',
      label: 'ENEMY',
      chapter: 7,
      weight: 1.0,
      evidence_summary: 'Hostile in chapter 7',
      metadata: {},
    },
  ],
};

const mockGraphCh2: GenericGraphReadModel = {
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 2,
    min_visible_chapter: 1,
    max_visible_chapter: 2,
    future_information_excluded: true,
  },
  nodes: [
    { id: 'char-lyra', node_type: 'CHARACTER', label: 'Lyra', chapter: 1, metadata: {} },
  ],
  edges: [],
};

// Inspector probe component to verify inspector payload integration
const InspectorInspector: React.FC = () => {
  const { isInspectorOpen, inspectorPayload } = useShellContext();
  if (!isInspectorOpen || !inspectorPayload) return null;
  return (
    <div data-testid="inspector-panel-probe">
      <div data-testid="inspector-title">{inspectorPayload.title}</div>
      <div data-testid="inspector-badge">{inspectorPayload.badge?.label}</div>
    </div>
  );
};

const renderGraphPage = (initialChapter = 10, seriesId = 'series-chrono-101') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/${seriesId}/graph?chapter=${initialChapter}`]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
          <ShellProvider>
            <Routes>
              <Route
                path="/series/:seriesId/graph"
                element={
                  <>
                    <GraphPage />
                    <InspectorInspector />
                  </>
                }
              />
              <Route
                path="/series/:seriesId/characters/:characterId"
                element={<div data-testid="character-profile-mock">Profile View Mock</div>}
              />
            </Routes>
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('GraphPage — Relationship Graph Intelligence Experience (Phase 6.6)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders graph nodes and header metrics truthfully from backend read model', () => {
    const useStoryGraphSpy = vi
      .spyOn(intelligenceQueriesMod, 'useStoryGraph')
      .mockReturnValue({
        data: mockGraphCh10,
        isLoading: false,
        isError: false,
        error: null,
      } as any);

    renderGraphPage(10, 'series-chrono-101');

    // Header metrics
    expect(screen.getByText('Relationship Graph Intelligence')).not.toBeNull();
    expect(screen.getByText('Ch. 10')).not.toBeNull();
    expect(screen.getByText('3 Characters')).not.toBeNull();
    expect(screen.getByText('2 Relationships')).not.toBeNull();

    // Viewport container is rendered
    expect(screen.getByTestId('graph-viewport-container')).not.toBeNull();

    // Verify spy was called with relationship graph_type and correct series & chapter
    expect(useStoryGraphSpy).toHaveBeenCalledWith('series-chrono-101', 10, 'relationship');
  });

  it('enforces Temporal Firewall: does not render future nodes or relationships at Ch. 2', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphCh2,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(2, 'series-chrono-101');

    expect(screen.getByText('Ch. 2')).not.toBeNull();
    expect(screen.getByTestId('graph-character-count-badge').textContent).toContain('1 Character');
    expect(screen.getByTestId('graph-relationship-count-badge').textContent).toContain('0 Relationships');
  });

  it('enforces Series Isolation: queries are scoped strictly by seriesId', () => {
    const useStoryGraphSpy = vi
      .spyOn(intelligenceQueriesMod, 'useStoryGraph')
      .mockReturnValue({
        data: {
          ...mockGraphCh10,
          temporal_context: { ...mockGraphCh10.temporal_context, series_id: 'series-nebula-999' },
        },
        isLoading: false,
        isError: false,
        error: null,
      } as any);

    renderGraphPage(10, 'series-nebula-999');

    expect(useStoryGraphSpy).toHaveBeenCalledWith('series-nebula-999', 10, 'relationship');
  });

  it('verifies No N+1 Contract: 0 character profile queries are dispatched during graph rendering', () => {
    const useCharacterProfileSpy = vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile');
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(10, 'series-chrono-101');

    // Crucial Performance Contract: Loading a graph with multiple nodes must NEVER call useCharacterProfile
    expect(useCharacterProfileSpy).not.toHaveBeenCalled();
  });

  it('integrates selection summary and opens Inspector with character details', async () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(10, 'series-chrono-101');

    // Initially selection summary shows prompt
    expect(screen.getByTestId('graph-selection-empty')).not.toBeNull();

    // Simulate clicking a node via custom character node component or DOM element
    // Custom node buttons have aria-label `Character Node: Lyra`
    const lyraNodeBtn = screen.getByLabelText('Character Node: Lyra');
    fireEvent.click(lyraNodeBtn);

    // Context summary appears
    expect(screen.getByTestId('graph-selection-summary')).not.toBeNull();
    expect(screen.getByTestId('selected-character-name').textContent).toContain('Lyra');
    expect(screen.getByText('Connections (1)')).not.toBeNull();
    expect(screen.getByTestId('connection-counterpart-name').textContent).toContain('Kael');
    expect(screen.getByText('ALLIED')).not.toBeNull();

    // Trigger inspector
    const inspectBtn = screen.getByTestId('inspect-character-btn');
    fireEvent.click(inspectBtn);

    expect(screen.getByTestId('inspector-panel-probe')).not.toBeNull();
    expect(screen.getByTestId('inspector-title').textContent).toContain('Lyra');
    expect(screen.getByTestId('inspector-badge').textContent).toContain('CHARACTER');
  });

  it('allows semantic navigation to character profile preserving seriesId and chapter', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(10, 'series-chrono-101');

    const kaelNodeBtn = screen.getByLabelText('Character Node: Kael');
    fireEvent.click(kaelNodeBtn);

    const profileLink = screen.getByTestId('view-profile-link').closest('a');
    expect(profileLink?.getAttribute('href')).toBe(
      '/series/series-chrono-101/characters/char-kael?chapter=10'
    );
  });

  it('renders loading state truthfully', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(10, 'series-chrono-101');
    expect(screen.getByTestId('graph-loading-state')).not.toBeNull();
  });

  it('renders error state truthfully with retry ability', () => {
    const refetchMock = vi.fn();
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error('Database disconnected'),
      refetch: refetchMock,
    } as any);

    renderGraphPage(10, 'series-chrono-101');
    expect(screen.getByTestId('graph-error-state')).not.toBeNull();
    expect(screen.getByText('Failed to Load Relationship Graph')).not.toBeNull();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(refetchMock).toHaveBeenCalled();
  });

  it('renders empty state truthfully when no nodes exist at current horizon', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: {
        temporal_context: {
          series_id: 'series-chrono-101',
          reader_chapter: 1,
          min_visible_chapter: 1,
          max_visible_chapter: 1,
          future_information_excluded: true,
        },
        nodes: [],
        edges: [],
      },
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(1, 'series-chrono-101');
    expect(screen.getByTestId('graph-empty-state')).not.toBeNull();
    expect(screen.getByText('No Relationships Known')).not.toBeNull();
  });

  it('renders graph relationship topology legend', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderGraphPage(10, 'series-chrono-101');

    expect(screen.getByTestId('graph-legend')).not.toBeNull();
    expect(screen.getByText('Relationship Topology Legend')).not.toBeNull();
    expect(screen.getByText('Allied / Friend')).not.toBeNull();
    expect(screen.getByText('Enemy / Rival')).not.toBeNull();
  });

  it('supports local defense-in-depth search without triggering backend requests', () => {
    const useStoryGraphSpy = vi
      .spyOn(intelligenceQueriesMod, 'useStoryGraph')
      .mockReturnValue({
        data: mockGraphCh10,
        isLoading: false,
        isError: false,
        error: null,
      } as any);

    renderGraphPage(10, 'series-chrono-101');

    const searchInput = screen.getByPlaceholderText('Focus character in graph...');
    fireEvent.change(searchInput, { target: { value: 'Lord Vane' } });

    // Local count indicator shows filtered result
    expect(screen.getByText('Showing 1 of 3 characters')).not.toBeNull();

    // Query parameters remain strictly seriesId, chapter, and 'relationship' (no backend search params sent)
    expect(useStoryGraphSpy).toHaveBeenLastCalledWith('series-chrono-101', 10, 'relationship');
  });
});
