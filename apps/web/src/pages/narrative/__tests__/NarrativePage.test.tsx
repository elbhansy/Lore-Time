import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider, useShellContext } from '../../../state/shell/shell-context';
import { NarrativePage } from '../NarrativePage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import {
  TimelineReadModel,
  StoryOverviewReadModel,
  GenericGraphReadModel,
  CharacterArcResponse,
} from '../../../api/contracts/read-models';

// Mock Discovery Data: Timeline Feed (Ch. 1 - 10)
const mockTimelineData: TimelineReadModel = {
  temporal_context: {
    series_id: 'series-alpha',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  from_chapter: 1,
  to_chapter: 10,
  total_events: 2,
  milestones: [
    {
      milestone_id: 'm-1',
      character_id: 'char-lyra',
      chapter: 3,
      sequence: 1,
      event_id: 'evt-1',
      milestone_type: 'FIRST_APPEARANCE',
      description: 'Lyra arrives in Sol',
      previous_state: {},
      new_state: { status: 'alive' },
      is_canonical: true,
    },
    {
      milestone_id: 'm-2',
      character_id: 'char-lyra',
      chapter: 7,
      sequence: 2,
      event_id: 'evt-2',
      milestone_type: 'RANK_CHANGE',
      description: 'Lyra ascends to Adept',
      previous_state: { rank: 'Novice' },
      new_state: { rank: 'Adept' },
      is_canonical: true,
    },
  ],
  turning_points: [
    {
      turning_point_id: 'tp-1',
      character_id: 'char-lyra',
      chapter: 8,
      sequence: 1,
      event_id: 'evt-3',
      turning_point_type: 'POWER_BREAKTHROUGH',
      significance: 'CRITICAL',
      description: 'Chronolith core resonant awakening',
      affected_dimensions: ['power', 'rank'],
      previous_state: {},
      resulting_state: { power: 500 },
      is_analytical: true,
    },
  ],
  pagination: { limit: 100, offset: 0, total_count: 2, has_more: false },
  events: [],
};

// Mock Discovery Data: Story Overview
const mockOverviewData: StoryOverviewReadModel = {
  series_id: 'series-alpha',
  series_title: 'The Sol Chronolith',
  temporal_context: {
    series_id: 'series-alpha',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  total_chapters_visible: 10,
  total_events_visible: 15,
  total_characters_visible: 2,
  total_factions_visible: 1,
  total_relationships_active: 1,
  recent_turning_points: mockTimelineData.turning_points,
  recent_events: [],
  active_phases_by_character: {
    'char-lyra': 'Adept of the Sun',
    'char-kael': 'Sentinel of Sol',
  },
};

// Mock Discovery Data: Generic Graph (Characters Roster)
const mockGraphData: GenericGraphReadModel = {
  temporal_context: {
    series_id: 'series-alpha',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  nodes: [
    { id: 'char-lyra', node_type: 'CHARACTER', label: 'Lyra Valen', chapter: 3, metadata: {} },
    { id: 'char-kael', node_type: 'CHARACTER', label: 'Kaelen Thorne', chapter: 1, metadata: {} },
  ],
  edges: [],
};

// Mock Deep Arc Response for Lyra
const mockLyraArcResponse: CharacterArcResponse = {
  series_id: 'series-alpha',
  character_id: 'char-lyra',
  reader_chapter: 10,
  start_chapter: 3,
  end_chapter: 10,
  milestones: mockTimelineData.milestones,
  turning_points: mockTimelineData.turning_points,
  phases: [
    {
      phase_id: 'phase-lyra-1',
      character_id: 'char-lyra',
      phase_number: 1,
      title: 'Novice of Sol',
      from_chapter: 3,
      to_chapter: 6,
      milestone_ids: ['m-1'],
      is_active_at_horizon: false,
    },
    {
      phase_id: 'phase-lyra-2',
      character_id: 'char-lyra',
      phase_number: 2,
      title: 'Adept of the Sun',
      from_chapter: 7,
      to_chapter: 10,
      milestone_ids: ['m-2'],
      turning_point_id: 'tp-1',
      dominant_faction: 'Solar Order',
      rank_at_phase_end: 'Adept',
      is_active_at_horizon: true,
    },
  ],
  trajectory: {
    total_milestones: 2,
    total_turning_points: 1,
    total_phases: 2,
    current_status: 'alive',
    current_rank: 'Adept',
    current_faction: 'Solar Order',
    total_skills_unlocked: 3,
    total_relationships: 2,
    highest_significance: 'CRITICAL',
  },
};

// Inspector Consumer Helper to intercept openInspector calls
let latestInspectorPayload: any = null;
const InspectorSpy: React.FC = () => {
  const { inspectorPayload } = useShellContext();
  latestInspectorPayload = inspectorPayload;
  return null;
};

const renderNarrativePage = (
  initialEntries: string[] = ['/series/series-alpha/narrative?chapter=10']
) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <Routes>
          <Route
            path="/series/:seriesId/narrative"
            element={
              <TemporalProvider seriesId="series-alpha" defaultChapter={10} totalChapters={200}>
                <ShellProvider>
                  <InspectorSpy />
                  <NarrativePage />
                </ShellProvider>
              </TemporalProvider>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('NarrativePage Integration Tests (Phase 6.8)', () => {
  let characterArcSpy: any;

  beforeEach(() => {
    vi.clearAllMocks();
    latestInspectorPayload = null;

    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraphData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    characterArcSpy = vi.spyOn(intelligenceQueriesMod, 'useCharacterArc').mockImplementation(
      (seriesId, characterId, chapter, enabled) => {
        if (!enabled || !characterId) {
          return { data: undefined, isLoading: false, isError: false } as any;
        }
        return { data: mockLyraArcResponse, isLoading: false, isError: false } as any;
      }
    );
  });

  it('Test 1: Renders Narrative Header with authoritative temporal horizon and metrics', () => {
    renderNarrativePage();

    expect(screen.getByTestId('narrative-header')).not.toBeNull();
    expect(screen.getByText('Narrative Intelligence Experience')).not.toBeNull();
    expect(screen.getAllByText(/Known Through Ch\. 10/i).length).toBeGreaterThan(0);
    expect(screen.getByText('Chapter 10 / 200')).not.toBeNull();
  });

  it('Test 2: Zero N+1 Contract — initial render triggers 0 deep character arc requests', () => {
    renderNarrativePage();

    // Verify useCharacterArc was called with enabled=false (0 deep requests executed)
    expect(characterArcSpy).toHaveBeenCalledWith(
      'series-alpha',
      null,
      10,
      false
    );
  });

  it('Test 3: Character Selection triggers exactly 1 deep character arc request', () => {
    renderNarrativePage();

    // Find and click Lyra's character pill in the explorer
    const lyraButton = screen.getByRole('button', { name: /Lyra Valen/i });
    fireEvent.click(lyraButton);

    // Verify useCharacterArc was called with enabled=true for char-lyra
    expect(characterArcSpy).toHaveBeenCalledWith(
      'series-alpha',
      'char-lyra',
      10,
      true
    );
  });

  it('Test 4: Temporal Firewall — milestones beyond readerChapter are never visible', () => {
    // Inject a future milestone in timeline feed
    const futureTimelineData = {
      ...mockTimelineData,
      milestones: [
        ...mockTimelineData.milestones,
        {
          milestone_id: 'm-future',
          character_id: 'char-kael',
          chapter: 15,
          sequence: 1,
          event_id: 'evt-future',
          milestone_type: 'DEATH',
          description: 'Future death spoiler',
          previous_state: {},
          new_state: {},
          is_canonical: true,
        },
      ],
    };

    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: futureTimelineData,
      isLoading: false,
      isError: false,
    } as any);

    renderNarrativePage();

    expect(screen.queryByText('Future death spoiler')).toBeNull();
  });

  it('Test 5: Backward Temporal Navigation — stale future character selection is cleared', () => {
    // Start with char-lyra selected who only appears in Ch. 3
    // If graph returns nodes only introduced at Ch. 1, char-lyra is not present
    const restrictedGraphData: GenericGraphReadModel = {
      ...mockGraphData,
      nodes: [{ id: 'char-kael', node_type: 'CHARACTER', label: 'Kaelen Thorne', chapter: 1, metadata: {} }],
    };

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: restrictedGraphData,
      isLoading: false,
      isError: false,
    } as any);

    renderNarrativePage(['/series/series-alpha/narrative?chapter=2&characterId=char-lyra']);

    // Since char-lyra is not in visible characters at Ch. 2, deep arc is disabled
    expect(characterArcSpy).toHaveBeenCalledWith('series-alpha', null, 2, false);
    expect(screen.getByText('No Character Selected')).not.toBeNull();
  });

  it('Test 6: Deep Inspector Integration — clicking inspect on milestone opens inspector payload', () => {
    renderNarrativePage();

    const milestonesList = screen.getByTestId('arc-milestones-list');
    const milestoneInspectBtn = milestonesList.querySelector('button');
    expect(milestoneInspectBtn).not.toBeNull();
    fireEvent.click(milestoneInspectBtn!);

    expect(latestInspectorPayload).not.toBeNull();
    expect(latestInspectorPayload.title).toContain('Milestone: FIRST_APPEARANCE');
    expect(latestInspectorPayload.subtitle).toContain('Character: char-lyra');
  });

  it('Test 7: Turning Point Inspection opens detailed analytical modal', () => {
    renderNarrativePage();

    const turningPointsList = screen.getByTestId('turning-points-list');
    const tpInspectBtn = turningPointsList.querySelector('button');
    expect(tpInspectBtn).not.toBeNull();
    fireEvent.click(tpInspectBtn!);

    expect(latestInspectorPayload).not.toBeNull();
    expect(latestInspectorPayload.title).toContain('Turning Point');
    expect(latestInspectorPayload.title).toContain('POWER BREAKTHROUGH');
  });
});
