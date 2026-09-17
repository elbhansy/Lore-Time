import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TemporalProvider } from '../../../state/temporal/temporal-context';
import { ShellProvider } from '../../../state/shell/shell-context';
import { CharacterProfilePage } from '../CharacterProfilePage';
import * as intelligenceQueriesMod from '../../../features/temporal/queries/useIntelligenceQueries';
import {
  CharacterReadModel,
  TemporalNarrativeCausalExplanationDTO,
} from '../../../api/contracts/read-models';

const mockCharacterProfile: CharacterReadModel = {
  character_id: 'char-lyra',
  series_id: 'series-chrono-101',
  name: 'Lyra',
  temporal_context: {
    series_id: 'series-chrono-101',
    reader_chapter: 15,
    min_visible_chapter: 1,
    max_visible_chapter: 15,
    future_information_excluded: true,
  },
  status: 'alive',
  rank: 'ADEPT',
  faction_id: 'faction-solar-guard',
  unlocked_skills: ['Solar Flare', 'Sun Shield'],
  active_relationships_count: 3,
  total_milestones_reached: 2,
  total_turning_points_passed: 1,
  current_phase_title: 'Awakened Flame',
  phases: [
    {
      phase_id: 'phase-1',
      character_id: 'char-lyra',
      phase_number: 1,
      title: 'Dormant Initiate',
      from_chapter: 1,
      to_chapter: 10,
      milestone_ids: ['ms-1'],
      dominant_faction: null,
      rank_at_phase_end: 'INITIATE',
      is_active_at_horizon: false,
    },
    {
      phase_id: 'phase-2',
      character_id: 'char-lyra',
      phase_number: 2,
      title: 'Awakened Flame',
      from_chapter: 11,
      to_chapter: 15,
      milestone_ids: ['ms-2'],
      dominant_faction: 'faction-solar-guard',
      rank_at_phase_end: 'ADEPT',
      is_active_at_horizon: true,
    },
  ],
  milestones: [
    {
      milestone_id: 'ms-1',
      character_id: 'char-lyra',
      chapter: 1,
      sequence: 1,
      event_id: 'evt-1',
      milestone_type: 'ORIGIN',
      description: 'Awakens in crystalline desert',
      previous_state: {},
      new_state: { status: 'alive' },
      is_canonical: true,
    },
    {
      milestone_id: 'ms-2',
      character_id: 'char-lyra',
      chapter: 15,
      sequence: 2,
      event_id: 'evt-15',
      milestone_type: 'RANK_ASCENSION',
      description: 'Unlocks Solar Core and reaches Adept rank',
      previous_state: { rank: 'INITIATE' },
      new_state: { rank: 'ADEPT' },
      is_canonical: true,
    },
  ],
  turning_points: [
    {
      turning_point_id: 'tp-1',
      character_id: 'char-lyra',
      chapter: 10,
      sequence: 1,
      event_id: 'evt-10',
      turning_point_type: 'BETRAYAL',
      significance: 'critical',
      description: 'Sabotages Solar Citadel and goes rogue',
      affected_dimensions: ['AFFILIATION', 'POWER'],
      previous_state: { faction: 'faction-solar-guard' },
      resulting_state: { faction: null },
      is_analytical: true,
    },
  ],
};

const mockCausality: TemporalNarrativeCausalExplanationDTO = {
  explanation_id: 'exp-lyra-1',
  series_id: 'series-chrono-101',
  explanation_type: 'CHARACTER_TRAJECTORY',
  reader_chapter: 15,
  focus_id: 'char-lyra',
  headline: 'Betrayal and Core Awakening Driven by Citadel Fall',
  narrative_steps: [
    {
      step_id: 'step-1',
      series_id: 'series-chrono-101',
      chapter: 10,
      source_event_id: 'evt-10',
      target_event_id: 'evt-15',
      relation_type: 'DIRECT_CAUSE',
      derivation_type: 'DETERMINISTIC',
      confidence: 'CERTAIN',
      affected_entities: ['char-lyra'],
      state_change_summary: 'Citadel sabotage forced survival awakening',
      impact_dimensions: ['SURVIVAL', 'POWER'],
    },
  ],
  narrative_paths: [
    {
      path_id: 'path-1',
      series_id: 'series-chrono-101',
      root_event_id: 'evt-10',
      terminal_event_id: 'evt-15',
      start_chapter: 10,
      end_chapter: 15,
      depth: 2,
      cumulative_impact_score: 1.8,
      impact_dimensions: ['POWER', 'SURVIVAL'],
      steps: [
        {
          step_id: 'step-1',
          series_id: 'series-chrono-101',
          chapter: 10,
          source_event_id: 'evt-10',
          target_event_id: 'evt-15',
          relation_type: 'DIRECT_CAUSE',
          derivation_type: 'DETERMINISTIC',
          confidence: 'CERTAIN',
          affected_entities: ['char-lyra'],
          state_change_summary: 'Citadel sabotage forced survival awakening',
          impact_dimensions: ['SURVIVAL', 'POWER'],
        },
      ],
    },
  ],
  turning_point_syntheses: [],
  intersected_milestone_ids: ['ms-1', 'ms-2'],
  conflicts: [],
  impact_breakdown: { POWER: 2, SURVIVAL: 1 },
  summary: {},
};

const renderCharacterProfilePage = (initialChapter = 15, characterId = 'char-lyra', seriesId = 'series-chrono-101') => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/series/${seriesId}/characters/${characterId}?chapter=${initialChapter}`]}>
        <TemporalProvider seriesId={seriesId} defaultChapter={initialChapter}>
          <ShellProvider>
            <Routes>
              <Route path="/series/:seriesId/characters/:characterId" element={<CharacterProfilePage />} />
            </Routes>
          </ShellProvider>
        </TemporalProvider>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('CharacterProfilePage — Character Intelligence Profile (Phase 6.5)', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('renders character identity banner with authoritative temporal horizon and metrics', () => {
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: mockCharacterProfile,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: mockCausality,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(15, 'char-lyra');

    expect(screen.getByRole('heading', { level: 1, name: 'Lyra' })).not.toBeNull();
    expect(screen.getAllByText('Awakened Flame').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('ADEPT')).not.toBeNull();
    expect(screen.getAllByText(/Known Through Ch. 15/i).length).toBeGreaterThanOrEqual(1);
  });

  it('renders character arc phases and milestones chronologically', () => {
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: mockCharacterProfile,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: mockCausality,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(15, 'char-lyra');

    expect(screen.getByText('Dormant Initiate')).not.toBeNull();
    expect(screen.getByText('Awakens in crystalline desert')).not.toBeNull();
    expect(screen.getByText('Unlocks Solar Core and reaches Adept rank')).not.toBeNull();
  });

  it('renders authoritative turning points with significance badge', () => {
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: mockCharacterProfile,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: mockCausality,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(15, 'char-lyra');

    expect(screen.getByText('Sabotages Solar Citadel and goes rogue')).not.toBeNull();
    expect(screen.getByText('critical')).not.toBeNull();
  });

  it('renders narrative synthesis clearly distinguished from canonical facts', () => {
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: mockCharacterProfile,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: mockCausality,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(15, 'char-lyra');

    expect(screen.getByText('NARRATIVE SYNTHESIS')).not.toBeNull();
    expect(screen.getByText('Betrayal and Core Awakening Driven by Citadel Fall')).not.toBeNull();
  });

  it('TEMPORAL FIREWALL: blocks unintroduced characters from leaking future facts', () => {
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: {
        ...mockCharacterProfile,
        status: 'unintroduced',
      },
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(5, 'char-lyra');

    expect(screen.getByText(/Character Not Introduced \(Spoiler Firewall\)/i)).not.toBeNull();
    expect(screen.queryByText('Awakened Flame')).toBeNull();
  });

  it('renders ErrorState with retry callback when profile request fails', () => {
    const refetchProfile = vi.fn();
    vi.spyOn(intelligenceQueriesMod, 'useCharacterProfile').mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: 'Character not found', status: 404 },
      refetch: refetchProfile,
    } as any);

    vi.spyOn(intelligenceQueriesMod, 'useCharacterNarrativeCausality').mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    } as any);

    renderCharacterProfilePage(15, 'char-ghost');

    expect(screen.getByRole('heading', { level: 4, name: /Character Not Found/i })).not.toBeNull();
    const retryBtn = screen.getByRole('button', { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(refetchProfile).toHaveBeenCalled();
  });
});
