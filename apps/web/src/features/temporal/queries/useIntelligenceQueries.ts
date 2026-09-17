import { useQuery, UseQueryResult } from '@tanstack/react-query';
import { intelligenceQueries } from '../../../api/queries/intelligence-queries';
import {
  StoryOverviewReadModel,
  TimelineReadModel,
  CharacterReadModel,
  GenericGraphReadModel,
  TemporalNarrativeCausalExplanationDTO,
  CharacterArcResponse,
  TemporalComparisonResponse,
} from '../../../api/contracts/read-models';
import { NormalizedApiError } from '../../../api/client/api-client';

export const intelligenceQueryKeys = {
  all: ['intelligence'] as const,
  overview: (seriesId: string, chapter: number) => ['intelligence', 'overview', seriesId, chapter] as const,
  timeline: (seriesId: string, chapter: number, from?: number, to?: number, limit?: number, offset?: number) =>
    ['intelligence', 'timeline', seriesId, chapter, { from, to, limit, offset }] as const,
  character: (seriesId: string, characterId: string, chapter: number) =>
    ['intelligence', 'character', seriesId, characterId, chapter] as const,
  graph: (seriesId: string, chapter: number, graphType: string) =>
    ['intelligence', 'graph', seriesId, chapter, graphType] as const,
  eventNarrative: (seriesId: string, eventId: string, chapter: number, maxDepth: number) =>
    ['intelligence', 'event-narrative', seriesId, eventId, chapter, maxDepth] as const,
  characterCausality: (seriesId: string, characterId: string, chapter: number, maxDepth: number) =>
    ['intelligence', 'character-causality', seriesId, characterId, chapter, maxDepth] as const,
  characterArc: (seriesId: string, characterId: string, chapter: number) =>
    ['intelligence', 'character-arc', seriesId, characterId, chapter] as const,
  temporalComparison: (seriesId: string, fromChapter: number, toChapter: number, readerChapter: number) =>
    ['intelligence', 'temporal-comparison', seriesId, fromChapter, toChapter, readerChapter] as const,
};

export function useStoryOverview(
  seriesId: string,
  chapter: number,
  enabled = true
): UseQueryResult<StoryOverviewReadModel, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.overview(seriesId, chapter),
    queryFn: ({ signal }) => intelligenceQueries.getStoryOverview(seriesId, chapter, signal),
    enabled: enabled && !!seriesId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useTimelineFeed(
  seriesId: string,
  chapter: number,
  options: { from?: number; to?: number; limit?: number; offset?: number } = {},
  enabled = true
): UseQueryResult<TimelineReadModel, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.timeline(seriesId, chapter, options.from, options.to, options.limit, options.offset),
    queryFn: ({ signal }) => intelligenceQueries.getTimelineFeed(seriesId, chapter, { ...options, signal }),
    enabled: enabled && !!seriesId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useCharacterProfile(
  seriesId: string,
  characterId: string,
  chapter: number,
  enabled = true
): UseQueryResult<CharacterReadModel, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.character(seriesId, characterId, chapter),
    queryFn: ({ signal }) => intelligenceQueries.getCharacterProfile(seriesId, characterId, chapter, signal),
    enabled: enabled && !!seriesId && !!characterId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useStoryGraph(
  seriesId: string,
  chapter: number,
  graphType: 'causal' | 'relationship' = 'causal',
  enabled = true
): UseQueryResult<GenericGraphReadModel, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.graph(seriesId, chapter, graphType),
    queryFn: ({ signal }) => intelligenceQueries.getIntelligenceGraph(seriesId, chapter, graphType, signal),
    enabled: enabled && !!seriesId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useEventNarrativeExplanation(
  seriesId: string,
  eventId: string,
  chapter: number,
  maxDepth = 4,
  enabled = true
): UseQueryResult<TemporalNarrativeCausalExplanationDTO, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.eventNarrative(seriesId, eventId, chapter, maxDepth),
    queryFn: ({ signal }) => intelligenceQueries.getEventNarrativeExplanation(seriesId, eventId, chapter, maxDepth, signal),
    enabled: enabled && !!seriesId && !!eventId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useCharacterNarrativeCausality(
  seriesId: string,
  characterId: string,
  chapter: number,
  maxDepth = 4,
  enabled = true
): UseQueryResult<TemporalNarrativeCausalExplanationDTO, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.characterCausality(seriesId, characterId, chapter, maxDepth),
    queryFn: ({ signal }) => intelligenceQueries.getCharacterNarrativeCausality(seriesId, characterId, chapter, maxDepth, signal),
    enabled: enabled && !!seriesId && !!characterId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useCharacterArc(
  seriesId: string,
  characterId: string | null,
  chapter: number,
  enabled = true
): UseQueryResult<CharacterArcResponse, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.characterArc(seriesId, characterId || '', chapter),
    queryFn: ({ signal }) => intelligenceQueries.getCharacterArc(seriesId, characterId || '', chapter, signal),
    enabled: enabled && !!seriesId && !!characterId && chapter >= 1,
    staleTime: 60_000,
  });
}

export function useTemporalComparison(
  seriesId: string,
  fromChapter: number,
  toChapter: number,
  readerChapter: number,
  enabled = true
): UseQueryResult<TemporalComparisonResponse, NormalizedApiError> {
  return useQuery({
    queryKey: intelligenceQueryKeys.temporalComparison(seriesId, fromChapter, toChapter, readerChapter),
    queryFn: ({ signal }) =>
      intelligenceQueries.getTemporalComparison(seriesId, fromChapter, toChapter, readerChapter, signal),
    enabled: enabled && !!seriesId && fromChapter >= 1 && toChapter >= fromChapter && readerChapter >= toChapter,
    staleTime: 60_000,
  });
}
