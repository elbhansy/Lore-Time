import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider } from '../../../state/shell/shell-context';
import { CharactersPage } from '../CharactersPage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import { StoryOverviewReadModel, GenericGraphReadModel } from '../../../api/contracts/read-models';

const mockOverview: StoryOverviewReadModel = {
  series_id: 'series-chrono-101',
  series_title: 'Chrono Bounds',
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 10,
    min_visible_chapter: 1,
    max_visible_chapter: 10,
    future_information_excluded: true,
  },
  total_chapters_visible: 10,
  total_events_visible: 25,
  total_characters_visible: 2,
  total_factions_visible: 2,
  total_relationships_active: 1,
  recent_turning_points: [],
  recent_events: [],
  active_phases_by_character: {
    'char-lyra': 'Awakened Initiate',
    'char-kael': 'Solar Guard Defender',
  },
};

const mockGraph: GenericGraphReadModel = {
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
  ],
};

const renderCharactersPage = (initialChapter = 10, seriesId = 'series-chrono-101') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/${seriesId}/characters?chapter=${initialChapter}`]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
          <ShellProvider>
            <CharactersPage />
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CharactersPage — Character Intelligence Explorer (Phase 6.5)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders CharacterExplorerHeader with authoritative temporal boundary and total count', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraph,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(10);

    expect(screen.getByRole('heading', { level: 1, name: /character intelligence explorer/i })).not.toBeNull();
    expect(screen.getByText(/Known Through Ch. 10/i)).not.toBeNull();
    expect(screen.getByText('Lyra')).not.toBeNull();
    expect(screen.getByText('Kael')).not.toBeNull();
  });

  it('filters visible characters when searching by name or ID', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraph,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(10);

    const searchInput = screen.getByRole('searchbox', { name: /search characters/i });
    fireEvent.change(searchInput, { target: { value: 'lyra' } });

    expect(screen.getByText('Lyra')).not.toBeNull();
    expect(screen.queryByText('Kael')).toBeNull();
  });

  it('does NOT fetch individual deep character profiles on the Explorer page (Prevents N+1)', () => {
    const profileSpy = vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile');

    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraph,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(10);

    // useCharacterProfile should NOT be called at all for the explorer list!
    expect(profileSpy).not.toHaveBeenCalled();
  });

  it('renders semantic links to character profiles', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: mockOverview,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: mockGraph,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(10);

    const lyraLink = screen.getByRole('link', { name: 'Lyra' });
    expect(lyraLink.getAttribute('href')).toBe('/series/series-chrono-101/characters/char-lyra');
  });

  it('renders truthful EmptyState when horizon contains no introduced characters', () => {
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: {
        ...mockOverview,
        total_characters_visible: 0,
        active_phases_by_character: {},
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: {
        ...mockGraph,
        nodes: [],
        edges: [],
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(1);

    expect(screen.getByText(/no characters discovered yet/i)).not.toBeNull();
  });

  it('renders ErrorState with retry callback on API failure', () => {
    const refetchOverview = vi.fn();
    vi.spyOn(intelligenceQueriesMod, 'useStoryOverview').mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: 'Database query timeout', status: 500 },
      refetch: refetchOverview,
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useStoryGraph').mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharactersPage(10);

    expect(screen.getByText(/Failed to Load Characters/i)).not.toBeNull();
    expect(screen.getByText(/Database query timeout/i)).not.toBeNull();

    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(refetchOverview).toHaveBeenCalled();
  });
});
