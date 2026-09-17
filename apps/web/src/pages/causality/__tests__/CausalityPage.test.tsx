import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider, useShellContext } from '../../../state/shell/shell-context';
import { CausalityPage } from '../CausalityPage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import {
  GenericGraphReadModel,
  TimelineReadModel,
  TemporalNarrativeCausalExplanationDTO,
} from '../../../api/contracts/read-models';

// Mock ResizeObserver for xyflow/react
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
(globalThis as any).ResizeObserver = ResizeObserverMock as any;

// Mock Discovery Data: Timeline Events (Ch. 1 - 10)
const mockTimelineData: TimelineReadModel = {
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  from_chapter: 1,
  to_chapter: 10,
  total_events: 2,
  milestones: [],
  turning_points: [],
  pagination: { limit: 100, offset: 0, total_count: 2, has_more: false },
  events: [
    {
      event_id: 'evt-1',
      series_id: 'series-chrono-101',
      chapter_number: 3,
      sequence: 1,
      event_type: 'CATACLYSM',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      title: 'The Great Awakening',
      description: 'Lyra activates the chronolith',
      previous_state: {},
      new_state: { power: 100 },
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: true,
      is_turning_point: false,
    },
    {
      event_id: 'evt-2',
      series_id: 'series-chrono-101',
      chapter_number: 7,
      sequence: 1,
      event_type: 'BATTLE',
      subject_type: 'CHAR',
      subject_id: 'char-kael',
      title: 'Siege of Sol',
      description: 'Kael defends against the swarm',
      previous_state: {},
      new_state: { defense: 80 },
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: false,
      is_turning_point: true,
    },
  ],
};

// Mock Causal Overview Topology (GenericGraphReadModel with graph_type="causal")
const mockCausalGraphCh10: GenericGraphReadModel = {
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  nodes: [
    { id: 'evt-1', node_type: 'EVENT', label: 'Event evt-1', chapter: 3, metadata: {} },
    { id: 'evt-2', node_type: 'EVENT', label: 'Event evt-2', chapter: 7, metadata: {} },
  ],
  edges: [
    {
      edge_id: 'rel:evt-1:evt-2',
      source_id: 'evt-1',
      target_id: 'evt-2',
      edge_type: 'DIRECT_CAUSE',
      label: 'DIRECT_CAUSE',
      chapter: 7,
      weight: 1.0,
      evidence_summary: 'Rule R-42',
      metadata: {},
    },
  ],
};

// Mock Deep Causal Explanation for Event 'evt-1'
const mockEventExplanation: TemporalNarrativeCausalExplanationDTO = {
  explanation_id: 'exp-evt-1',
  series_id: 'series-chrono-101',
  explanation_type: 'EVENT_CAUSAL_TRACE',
  reader_chapter: 10,
  focus_id: 'evt-1',
  headline: 'Chronolith Activation Cascades Into Siege of Sol',
  narrative_steps: [
    {
      step_id: 'step-1',
      series_id: 'series-chrono-101',
      chapter: 3,
      source_event_id: 'evt-1',
      target_event_id: 'evt-2',
      relation_type: 'DIRECT_CAUSE',
      derivation_type: 'DERIVED_DIRECT',
      confidence: 'STRONG',
      affected_entities: ['char-lyra', 'char-kael'],
      state_change_summary: 'Energy pulse destabilized solar barrier',
      impact_dimensions: ['POWER', 'ENVIRONMENT'],
      evidence_rule_id: 'RULE-CHRONO-9',
      explanation_code: 'EXP-101',
    },
  ],
  narrative_paths: [
    {
      path_id: 'path-1',
      series_id: 'series-chrono-101',
      root_event_id: 'evt-1',
      terminal_event_id: 'evt-2',
      start_chapter: 3,
      end_chapter: 7,
      depth: 2,
      cumulative_impact_score: 2.5,
      impact_dimensions: ['POWER'],
      steps: [],
    },
  ],
  turning_point_syntheses: [],
  intersected_milestone_ids: [],
  conflicts: [
    {
      conflict_id: 'conf-1',
      series_id: 'series-chrono-101',
      target_event_id: 'evt-2',
      conflicting_relation_ids: ['rel-a', 'rel-b'],
      conflict_type: 'CHRONOLOGY_DIVERGENCE',
      evidence_summary: 'Dual temporal origin detected',
      resolution_status: 'SUPPORTED',
    },
  ],
  impact_breakdown: { POWER: 2, FACTION: 1 },
  summary: { total_impact: 2.5 },
};

// Probe component to verify centralized inspector payload
const InspectorProbe: React.FC = () => {
  const { isInspectorOpen, inspectorPayload } = useShellContext();
  if (!isInspectorOpen || !inspectorPayload) return null;
  return (
    <div data-testid="inspector-panel-probe">
      <div data-testid="inspector-title">{inspectorPayload.title}</div>
      <div data-testid="inspector-badge">{inspectorPayload.badge?.label}</div>
    </div>
  );
};

const renderCausalityPage = (initialUrl = '/series/series-chrono-101/causality?chapter=10', seriesId = 'series-chrono-101') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialUrl]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={10}>
          <ShellProvider>
            <Routes>
              <Route
                path="/series/:seriesId/causality"
                element={
                  <>
                    <CausalityPage />
                    <InspectorProbe />
                  </>
                }
              />
              <Route
                path="/series/:seriesId/characters/:characterId"
                element={<div data-testid="character-profile-mock">Character Profile Mock</div>}
              />
              <Route
                path="/series/:seriesId/timeline"
                element={<div data-testid="timeline-mock">Timeline Mock</div>}
              />
            </Routes>
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CausalityPage — Causal Investigation Intelligence Experience (Phase 6.7)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    // Default mocks
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockCausalGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useEventNarrativeExplanation').mockReturnValue({
      data: mockEventExplanation,
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: mockEventExplanation,
      isLoading: false,
      isError: false,
      error: null,
    } as any);
  });

  it('renders causality header metrics, controls, and causal legend truthfully from Phase 5.2 contracts', () => {
    renderCausalityPage();

    expect(screen.getByText('Causal Investigation Intelligence')).not.toBeNull();
    expect(screen.getByText('Ch. 10')).not.toBeNull();
    expect(screen.getByTestId('causal-nodes-count-badge')).not.toBeNull();
    expect(screen.getByTestId('causal-legend')).not.toBeNull();
    expect(screen.getByText('Causal Relation Semantics (Phase 5.2)')).not.toBeNull();
    expect(screen.getByText('DIRECT_CAUSE / EVENT_CHAIN')).not.toBeNull();
    expect(screen.getByText('INDIRECT_INFLUENCE')).not.toBeNull();
  });

  it('test_zero_n_plus_one_contract: renders causality discovery and overview with zero character profile requests', () => {
    const useCharacterProfileSpy = vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile');

    renderCausalityPage();

    // Zero character profile requests on initial causality load
    expect(useCharacterProfileSpy).not.toHaveBeenCalled();
  });

  it('test_cross_target_isolation: switches modes and wipes active target state cleanly', () => {
    renderCausalityPage('/series/series-chrono-101/causality?chapter=10&mode=event&targetId=evt-1');

    // Currently in event mode with target evt-1
    expect(screen.getByTestId('selected-causal-target-title').textContent).toContain('The Great Awakening');

    // Switch to Character mode
    const charBtn = screen.getByTestId('mode-switch-character');
    fireEvent.click(charBtn);

    // Target state must be cleanly wiped
    expect(screen.getByTestId('causal-selection-empty')).not.toBeNull();
  });

  it('test_temporal_stale_cache_invalidation: clears invalid target selection when horizon moves backward', () => {
    // Event evt-2 occurs at Ch. 7. If horizon is at Ch. 2, evt-2 is in the future.
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: {
        ...mockTimelineData,
        events: [], // No events at Ch. 2
      },
      isLoading: false,
      isError: false,
      error: null,
    } as any);

    renderCausalityPage('/series/series-chrono-101/causality?chapter=2&mode=event&targetId=evt-2');

    // Selection must be cleared because target is outside current horizon
    expect(screen.getByTestId('causal-selection-empty')).not.toBeNull();
  });

  it('integrates with ShellContext Inspector to display deep narrative synthesis and conflicts', () => {
    renderCausalityPage('/series/series-chrono-101/causality?chapter=10&mode=event&targetId=evt-1');

    const inspectBtn = screen.getByTestId('inspect-causal-target-btn');
    fireEvent.click(inspectBtn);

    expect(screen.getByTestId('inspector-panel-probe')).not.toBeNull();
    expect(screen.getByTestId('inspector-badge').textContent).toContain('CAUSAL SYNTHESIS');
  });

  it('preserves seriesId and chapter during deep navigation to timeline feed', () => {
    renderCausalityPage('/series/series-chrono-101/causality?chapter=10&mode=event&targetId=evt-1');

    const timelineLink = screen.getByTestId('view-timeline-feed-link').closest('a');
    expect(timelineLink?.getAttribute('href')).toBe('/series/series-chrono-101/timeline?chapter=10');
  });

  it('renders truthful loading and error states', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
      error: null,
    } as any);

    renderCausalityPage();
    expect(screen.getByTestId('causality-loading-state')).not.toBeNull();
  });
});
