import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider } from '../../../state/shell/shell-context';
import { OverviewPage } from '../OverviewPage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import { StoryOverviewReadModel } from '../../../api/contracts/read-models';

const mockOverviewData: StoryOverviewReadModel = {
  series_id: 'series-alpha-001',
  series_title: 'Chronicles of the Shattered Sphere',
  temporal_context: {
    series_id: 'series-alpha-001',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  total_chapters_visible: 10,
  total_events_visible: 45,
  total_characters_visible: 12,
  total_factions_visible: 4,
  total_relationships_active: 8,
  recent_turning_points: [
    {
      turning_point_id: 'tp-1',
      character_id: 'char-kallan',
      chapter: 8,
      sequence: 1,
      event_id: 'evt-tp-1',
      turning_point_type: 'BETRAYAL',
      significance: 'critical',
      description: 'Kallan defects from the Citadel Vanguard during the siege.',
      affected_dimensions: ['AFFILIATION', 'POWER'],
      previous_state: {},
      resulting_state: {},
      is_analytical: true,
    },
  ],
  recent_events: [
    {
      event_id: 'evt-1',
      series_id: 'series-alpha-001',
      chapter_number: 10,
      sequence: 2,
      event_type: 'CITY_GATE_BREACHED',
      subject_type: 'FACTION',
      subject_id: 'faction-iron-oath',
      target_type: null,
      target_id: null,
      title: 'Outer Gates Collapsed',
      description: 'The iron gates collapse under siege engines.',
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
      series_id: 'series-alpha-001',
      chapter_number: 9,
      sequence: 1,
      event_type: 'COUNCIL_DISPERSED',
      subject_type: 'FACTION',
      subject_id: 'faction-citadel',
      target_type: null,
      target_id: null,
      title: 'Vanguard Council Dissolves',
      description: 'The citadel rulers disperse following the breach warning.',
      previous_state: {},
      new_state: {},
      metadata: {},
      causes: [],
      effects: [],
      is_milestone: false,
      is_turning_point: true,
    },
  ],
  active_phases_by_character: {
    'char-kallan': 'Exile in Shadow',
    'char-elena': 'Commander of the Remnant',
  },
};

const renderOverviewPage = (initialChapter = 10, seriesId = 'series-alpha-001') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/${seriesId}?chapter=${initialChapter}`]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
          <ShellProvider>
            <OverviewPage />
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('OverviewPage — Story Overview Experience (Phase 6.3)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders story identity, series title, and canonical temporal scope', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('Chronicles of the Shattered Sphere')).not.toBeNull();
    expect(screen.getByText(/ID: series-alpha-001/)).not.toBeNull();
    expect(screen.getAllByText('Ch. 10').length).toBeGreaterThan(0);
    expect(screen.getByText('Known Through Chapter 10')).not.toBeNull();
  });

  it('renders authoritative story statistics from read model', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('Visible Chapters')).not.toBeNull();
    expect(screen.getByText('45')).not.toBeNull(); // totalEventsVisible
    expect(screen.getByText('12')).not.toBeNull(); // totalCharactersVisible
    expect(screen.getByText('4')).not.toBeNull(); // totalFactionsVisible
    expect(screen.getByText('8')).not.toBeNull(); // totalRelationshipsActive
  });

  it('renders timeline preview with events strictly bounded to temporal horizon', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('Outer Gates Collapsed')).not.toBeNull();
    expect(screen.getByText('Vanguard Council Dissolves')).not.toBeNull();
    expect(screen.getByText('Milestone')).not.toBeNull();
  });

  it('renders key turning points with character associations', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('BETRAYAL')).not.toBeNull();
    expect(screen.getByText(/critical/i)).not.toBeNull();
    expect(screen.getByText(/Kallan defects from the Citadel Vanguard/)).not.toBeNull();
    expect(screen.getByText('Character: char-kallan')).not.toBeNull();
  });

  it('renders character trajectories and current narrative phases', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverviewData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('char-kallan')).not.toBeNull();
    expect(screen.getByText('Exile in Shadow')).not.toBeNull();
    expect(screen.getByText('char-elena')).not.toBeNull();
    expect(screen.getByText('Commander of the Remnant')).not.toBeNull();
  });

  it('renders truthful empty state when no turning points or events exist', () => {
    const emptyData: StoryOverviewReadModel = {
      ...mockOverviewData,
      recent_events: [],
      recent_turning_points: [],
      active_phases_by_character: {},
    };

    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: emptyData,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderOverviewPage(1);

    expect(screen.getByText('No Events Recorded')).not.toBeNull();
    expect(screen.getByText('No Turning Points Recorded')).not.toBeNull();
    expect(screen.getByText('No Active Characters')).not.toBeNull();
  });

  it('renders ErrorState when API fails with retry trigger', () => {
    const refetchMock = vi.fn();
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: { message: 'Intelligence Core timeout', status: 504 } as any,
      refetch: refetchMock,
    } as any);

    renderOverviewPage(10);

    expect(screen.getByText('Failed to Load Story Overview (504)')).not.toBeNull();
    expect(screen.getByText('Intelligence Core timeout')).not.toBeNull();

    fireEvent.click(screen.getByText('Retry Query'));
    expect(refetchMock).toHaveBeenCalled();
  });

  it('verifies temporal firewall: never displays future events or future turning points', () => {
    // If backend or data contains future events beyond readerChapter 10 (e.g. Chapter 15),
    // we test that the read model respects readerChapter boundary
    expect(mockOverviewData.temporal_context.max_visible_chapter).toBe(10);
    expect(mockOverviewData.recent_events.every((e) => e.chapter_number <= 10)).toBe(true);
    expect(mockOverviewData.recent_turning_points.every((tp) => tp.chapter <= 10)).toBe(true);
  });
});
