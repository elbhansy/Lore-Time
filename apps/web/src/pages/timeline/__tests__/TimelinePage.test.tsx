import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider } from '../../../state/shell/shell-context';
import { TimelinePage } from '../TimelinePage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import { TimelineReadModel } from '../../../api/contracts/read-models';

const mockTimelineData: TimelineReadModel = {
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 15,
    min_visible_chapter: 1,
    max_visible_chapter: 15,
    future_information_excluded: true,
  },
  from_chapter: 1,
  to_chapter: 15,
  total_events: 4,
  milestones: [],
  turning_points: [],
  pagination: {
    limit: 50,
    offset: 0,
    total_count: 4,
    has_more: false,
  },
  events: [
    {
      event_id: 'evt-c1-1',
      series_id: 'series-chrono-101',
      chapter_number: 1,
      sequence: 1,
      event_type: 'CHARACTER_INTRODUCED',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      target_type: null,
      target_id: null,
      title: 'Lyra Awakening in Ruins',
      description: 'Lyra awakens amidst the crystalline desert of Aethel.',
      previous_state: {},
      new_state: { status: 'alive' },
      metadata: {},
      causes: [],
      effects: [
        {
          relation_id: 'rel-1-2',
          series_id: 'series-chrono-101',
          source_event_id: 'evt-c1-1',
          target_event_id: 'evt-c5-1',
          relation_type: 'DIRECT_CAUSE',
          derivation_type: 'DETERMINISTIC',
          confidence: 'CERTAIN',
          source_chapter: 1,
          target_chapter: 5,
          impact_score: 0.85,
          affected_entity_ids: ['char-lyra'],
          evidence: {
            rule_id: 'rule-temporal-precedence',
            explanation_code: 'CAUSAL_ORIGIN',
            source_event_ids: ['evt-c1-1'],
            target_event_id: 'evt-c5-1',
            temporal_basis: 'Ch. 1 precedes Ch. 5',
            metadata: {},
          },
          metadata: {},
        },
      ],
      is_milestone: true,
      is_turning_point: false,
    },
    {
      event_id: 'evt-c5-1',
      series_id: 'series-chrono-101',
      chapter_number: 5,
      sequence: 1,
      event_type: 'FACTION_JOINED',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      target_type: 'FACTION',
      target_id: 'faction-solar-guard',
      title: 'Enlistment in Solar Guard',
      description: 'Lyra pledges allegiance to the Solar Guard.',
      previous_state: {},
      new_state: { faction: 'faction-solar-guard' },
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: false,
      is_turning_point: false,
    },
    {
      event_id: 'evt-c10-1',
      series_id: 'series-chrono-101',
      chapter_number: 10,
      sequence: 1,
      event_type: 'BETRAYAL',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      target_type: 'FACTION',
      target_id: 'faction-solar-guard',
      title: 'Defection from Solar Guard',
      description: 'Lyra sabotages the citadel gates and escapes into the night.',
      previous_state: { faction: 'faction-solar-guard' },
      new_state: { faction: null },
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: false,
      is_turning_point: true,
    },
    {
      event_id: 'evt-c15-1',
      series_id: 'series-chrono-101',
      chapter_number: 15,
      sequence: 2,
      event_type: 'POWER_AWAKENED',
      subject_type: 'CHAR',
      subject_id: 'char-lyra',
      target_type: null,
      target_id: null,
      title: 'Solar Core Manifestation',
      description: 'Under severe peril, Lyra unlocks the dormant Solar Core.',
      previous_state: { power_rank: 'INITIATE' },
      new_state: { power_rank: 'ADEPT' },
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: true,
      is_turning_point: true,
    },
  ],
};

const renderTimelinePage = (initialChapter = 15, seriesId = 'series-chrono-101') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/${seriesId}/timeline?chapter=${initialChapter}`]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
          <ShellProvider>
            <TimelinePage />
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('TimelinePage — Timeline Intelligence Experience (Phase 6.4)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders TimelineHeader with authoritative temporal boundary and total counts', () => {
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderTimelinePage(15);

    expect(screen.getByText('Chronological Timeline Feed')).not.toBeNull();
    expect(screen.getByText('Known Through Ch. 15')).not.toBeNull();
    expect(screen.getByText(/Displaying 4 canonical events/)).not.toBeNull();
  });

  it('renders events chronologically grouped by chapter', () => {
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderTimelinePage(15);

    expect(screen.getByText('Chapter 1')).not.toBeNull();
    expect(screen.getByText('Chapter 5')).not.toBeNull();
    expect(screen.getByText('Chapter 10')).not.toBeNull();
    expect(screen.getByText('Chapter 15')).not.toBeNull();

    expect(screen.getByText('Lyra Awakening in Ruins')).not.toBeNull();
    expect(screen.getByText('Enlistment in Solar Guard')).not.toBeNull();
    expect(screen.getByText('Defection from Solar Guard')).not.toBeNull();
    expect(screen.getByText('Solar Core Manifestation')).not.toBeNull();
  });

  it('visually distinguishes turning points and milestones', () => {
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderTimelinePage(15);

    const turningPointBadges = screen.getAllByText('Turning Point');
    expect(turningPointBadges.length).toBe(2);

    const milestoneBadges = screen.getAllByText('Milestone');
    expect(milestoneBadges.length).toBe(2);
  });

  it('shows Current Reader Boundary marker on the latest visible chapter', () => {
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: mockTimelineData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderTimelinePage(15);

    expect(screen.getByText('Current Reader Boundary')).not.toBeNull();
    expect(screen.getByText(/Current Knowledge Horizon Reached/)).not.toBeNull();
  });

  it('TEMPORAL FIREWALL: strictly excludes events beyond readerChapter', () => {
    // Inject a rogue future event at Chapter 25 into mock data
    const dataWithFutureLeak: TimelineReadModel = {
      ...mockTimelineData,
      events: [
        ...mockTimelineData.events,
        {
          event_id: 'evt-c25-future',
          series_id: 'series-chrono-101',
          chapter_number: 25,
          sequence: 1,
          event_type: 'FUTURE_DISASTER',
          subject_type: 'WORLD',
          subject_id: 'world-prime',
          target_type: null,
          target_id: null,
          title: 'Cataclysm of the Third Sun',
          description: 'Future event that MUST NOT be rendered.',
          previous_state: {},
          new_state: {},
          metadata: {},
          causes: [],
          effects: [],
          is_milestone: false,
          is_turning_point: false,
        },
      ],
    };

    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: dataWithFutureLeak,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    // Render at horizon 15
    renderTimelinePage(15);

    // Chapter 25 future event must NOT be in the DOM
    expect(screen.queryByText('Cataclysm of the Third Sun')).toBeNull();
    expect(screen.queryByText('Chapter 25')).toBeNull();
  });

  it('renders truthful EmptyState when horizon has zero events', () => {
    const emptyTimeline: TimelineReadModel = {
      ...mockTimelineData,
      events: [],
      total_events: 0,
    };

    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: emptyTimeline,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderTimelinePage(1);

    expect(screen.getByText('No Events in Horizon')).not.toBeNull();
    expect(screen.getByText(/No story events exist between Chapter 1 and Chapter 1/)).not.toBeNull();
  });

  it('renders ErrorState with retry callback when API query fails', () => {
    const refetchMock = vi.fn();
    vi.spyOn(intelligenceQueriesMod, 'useTimelineFeed').mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Failed to stream timeline events', status: 500 } as any,
      refetch: refetchMock,
    } as any);

    renderTimelinePage(15);

    expect(screen.getByText('Failed to Load Timeline Stream (500)')).not.toBeNull();
    expect(screen.getByText('Failed to stream timeline events')).not.toBeNull();

    fireEvent.click(screen.getByText('Retry Query'));
    expect(refetchMock).toHaveBeenCalled();
  });
});
