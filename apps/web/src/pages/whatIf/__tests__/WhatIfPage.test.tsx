import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider } from '../../../state/shell/shell-context';
import { WhatIfPage } from '../WhatIfPage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import {
  GenericGraphReadModel,
  TimelineReadModel,
  TemporalComparisonResponse,
} from '../../../api/contracts/read-models';

// Mock timeline events up to Chapter 10
const mockTimelineDataCh10: TimelineReadModel = {
  temporal_context: {
    series_id: 'series-cf-101',
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
      series_id: 'series-cf-101',
      chapter_number: 3,
      sequence: 1,
      event_type: 'CATACLYSM',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      title: 'The Great Awakening',
      description: 'Lyra activates chronolith',
      previous_state: {},
      new_state: {},
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: true,
      is_turning_point: false,
    },
    {
      event_id: 'evt-2',
      series_id: 'series-cf-101',
      chapter_number: 7,
      sequence: 1,
      event_type: 'BATTLE',
      subject_type: 'CHAR',
      subject_id: 'char-kael',
      title: 'Siege of Sol',
      description: 'Battle of Sol fortress',
      previous_state: {},
      new_state: {},
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: false,
      is_turning_point: true,
    },
  ],
};

// Mock character relationship graph
const mockCharacterGraphCh10: GenericGraphReadModel = {
  temporal_context: {
    series_id: 'series-cf-101',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  nodes: [
    { id: 'char-lyra', node_type: 'character', label: 'Lyra', chapter: 3, metadata: {} },
    { id: 'char-kael', node_type: 'character', label: 'Kael', chapter: 7, metadata: {} },
  ],
  edges: [],
};

// Mock comparison simulation result
const mockComparisonData: TemporalComparisonResponse = {
  from_chapter: 3,
  to_chapter: 10,
  summary: {
    characters_introduced: 0,
    characters_removed: 1,
    power_changes: 1,
    skills_unlocked: 2,
    relationships_changed: 1,
  },
  character_changes: [
    {
      character_id: 'char-kael',
      change_type: 'CHANGED',
      before_status: 'alive',
      after_status: 'dead',
    },
  ],
  power_changes: [
    {
      character_id: 'char-lyra',
      before_rank: 'Adept',
      after_rank: 'Master',
    },
  ],
  relationship_changes: [
    {
      source_id: 'char-lyra',
      target_id: 'char-kael',
      change_type: 'CHANGED',
      before_type: 'ALLY',
      after_type: 'ENEMY',
    },
  ],
  skill_changes: [
    {
      character_id: 'char-kael',
      unlocked_skills: ['Temporal Shift', 'Void Shield'],
    },
  ],
};

const renderWhatIfPage = (seriesId = 'series-cf-101', initialRoute = `/series/${seriesId}/what-if?chapter=10`) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route
            path="/series/:seriesId/what-if"
            element={
              <TemporalProvider seriesId={seriesId}>
                <ShellProvider>
                  <WhatIfPage />
                </ShellProvider>
              </TemporalProvider>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('Phase 6.9 — WhatIfPage Counterfactual Intelligence Experience', () => {
  let mockTimelineSpy: any;
  let mockGraphSpy: any;
  let mockComparisonSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();

    mockTimelineSpy = vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineDataCh10,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    mockGraphSpy = vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockCharacterGraphCh10,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    mockComparisonSpy = vi.spyOn(intelligenceQueriesMod, 'useTemporalComparison').mockReturnValue({
      data: undefined,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);
  });

  it('1. Initial Render & Zero N+1: Renders page, baseline context, and empty state without profile requests', () => {
    renderWhatIfPage();

    expect(screen.getByTestId('what-if-page')).not.toBeNull();
    expect(screen.getByTestId('what-if-header')).not.toBeNull();
    expect(screen.getByTestId('canonical-context-bar')).not.toBeNull();
    expect(screen.getByTestId('scenario-builder')).not.toBeNull();
    expect(screen.getByTestId('what-if-empty-state')).not.toBeNull();
    expect(screen.getByTestId('counterfactual-safety-panel')).not.toBeNull();

    // Verify Zero N+1: discovery hooks called, but comparison is NOT executed yet
    expect(mockTimelineSpy).toHaveBeenCalled();
    expect(mockGraphSpy).toHaveBeenCalled();
    expect(mockComparisonSpy).toHaveBeenCalledWith('series-cf-101', 1, 10, 10, false);
  });

  it('2. Scenario Builder Configuration: Populates targets and submits scenario to active simulation', async () => {
    renderWhatIfPage();

    // Select target
    const targetSelect = screen.getByTestId('target-entity-select');
    fireEvent.change(targetSelect, { target: { value: 'char-lyra' } });

    // Verify Execute button is enabled
    const applyBtn = screen.getByTestId('apply-scenario-btn');
    expect((applyBtn as HTMLButtonElement).disabled).toBe(false);

    // Click Run Simulation
    fireEvent.click(applyBtn);

    // Scenario summary card becomes active
    await waitFor(() => {
      expect(screen.getByTestId('scenario-summary-card')).not.toBeNull();
      expect(screen.getByText('HYPOTHETICAL SCENARIO ACTIVE')).not.toBeNull();
    });
  });

  it('3. Counterfactual Simulation Execution: Dispatches comparison query and renders diff metrics & impact list', async () => {
    mockComparisonSpy.mockReturnValue({
      data: mockComparisonData,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWhatIfPage();

    // Select target and click Execute
    const targetSelect = screen.getByTestId('target-entity-select');
    fireEvent.change(targetSelect, { target: { value: 'char-kael' } });

    const applyBtn = screen.getByTestId('apply-scenario-btn');
    fireEvent.click(applyBtn);

    // Verify comparison metrics and impacts appear
    await waitFor(() => {
      expect(screen.getByTestId('counterfactual-comparison-card')).not.toBeNull();
      expect(screen.getByTestId('hypothetical-impact-list')).not.toBeNull();
    });

    // Verify impacted rows contain both CANONICAL and HYPOTHETICAL markers
    expect(screen.getAllByText(/char-kael/).length).toBeGreaterThan(0);
    expect(screen.getByText('alive')).not.toBeNull();
    expect(screen.getByText('→ dead')).not.toBeNull();
    expect(screen.getAllByText('NOT CANON').length).toBeGreaterThan(0);
  });

  it('4. Temporal Firewall (Backward Navigation N -> N-1): Invalidates hypothetical scenario if intervention > horizon', async () => {
    mockComparisonSpy.mockReturnValue({
      data: mockComparisonData,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWhatIfPage('series-cf-101', '/series/series-cf-101/what-if?chapter=10');

    // Configure scenario at chapter 10
    const targetSelect = screen.getByTestId('target-entity-select');
    fireEvent.change(targetSelect, { target: { value: 'char-kael' } });

    const chapterInput = screen.getByTestId('intervention-chapter-input');
    fireEvent.change(chapterInput, { target: { value: '10' } });

    const applyBtn = screen.getByTestId('apply-scenario-btn');
    fireEvent.click(applyBtn);

    await waitFor(() => {
      expect(screen.getByTestId('hypothetical-impact-list')).not.toBeNull();
    });

    // Step backward to Chapter 9
    const stepBackBtn = screen.getByTestId('temporal-step-back-btn');
    fireEvent.click(stepBackBtn);

    // Scenario at chapter 10 must be auto-cleared because it violates the new chapter 9 boundary
    await waitFor(() => {
      expect(screen.queryByTestId('hypothetical-impact-list')).toBeNull();
      expect(screen.getByTestId('what-if-empty-state')).not.toBeNull();
    });
  });

  it('5. Scenario Reset: Restores canonical state without mutating chapter or series', async () => {
    mockComparisonSpy.mockReturnValue({
      data: mockComparisonData,
      isLoading: false,
      isFetching: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderWhatIfPage();

    // Configure and apply scenario
    const targetSelect = screen.getByTestId('target-entity-select');
    fireEvent.change(targetSelect, { target: { value: 'char-lyra' } });
    fireEvent.click(screen.getByTestId('apply-scenario-btn'));

    await waitFor(() => {
      expect(screen.getByTestId('counterfactual-comparison-card')).not.toBeNull();
    });

    // Click Reset
    const resetBtn = screen.getByTestId('scenario-reset-btn');
    fireEvent.click(resetBtn);

    // Hypothetical results must disappear and empty state return
    await waitFor(() => {
      expect(screen.queryByTestId('counterfactual-comparison-card')).toBeNull();
      expect(screen.getByTestId('what-if-empty-state')).not.toBeNull();
    });

    // Reader horizon remains Chapter 10
    expect(screen.getByTestId('canonical-context-bar').textContent).toContain('Chapter 10');
  });

  it('6. Series Isolation: Series ID is strictly bound to context and queries', () => {
    renderWhatIfPage('series-alpha', '/series/series-alpha/what-if?chapter=5');

    expect(mockTimelineSpy).toHaveBeenCalledWith('series-alpha', 5, expect.anything(), true);
    expect(mockGraphSpy).toHaveBeenCalledWith('series-alpha', 5, 'relationship', true);
    expect(screen.getByTestId('counterfactual-safety-panel').textContent).toContain('series-alpha');
  });
});
