import { defaultApiClient, ApiClient } from '../client/api-client';
import {
  StoryOverviewReadModel,
  TimelineReadModel,
  CharacterReadModel,
  GenericGraphReadModel,
  TemporalNarrativeCausalExplanationDTO,
  CharacterArcResponse,
  TemporalComparisonResponse,
} from '../contracts/read-models';

/**
 * Phase 6.1 Intelligence Queries Service.
 *
 * Exposes scoped query methods communicating strictly with backend read models:
 * - GET /api/v1/series/{series_id}/intelligence/overview
 * - GET /api/v1/series/{series_id}/intelligence/timeline-feed
 * - GET /api/v1/series/{series_id}/intelligence/characters/{character_id}/profile
 * - GET /api/v1/series/{series_id}/intelligence/graph
 * - GET /api/v1/series/{series_id}/intelligence/event-narrative/{event_id}
 * - GET /api/v1/series/{series_id}/intelligence/character-narrative-causality/{character_id}
 * - GET /api/v1/series/{series_id}/intelligence/character-arc/{character_id}
 */
export class IntelligenceQueries {
  private client: ApiClient;

  constructor(client: ApiClient = defaultApiClient) {
    this.client = client;
  }

  public getStoryOverview(seriesId: string, chapter: number, signal?: AbortSignal): Promise<StoryOverviewReadModel> {
    const params = new URLSearchParams({ chapter: chapter.toString() });
    return this.client.get<StoryOverviewReadModel>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/overview?${params.toString()}`,
      { signal }
    );
  }

  public getTimelineFeed(
    seriesId: string,
    chapter: number,
    options: { from?: number; to?: number; limit?: number; offset?: number; signal?: AbortSignal } = {}
  ): Promise<TimelineReadModel> {
    const params = new URLSearchParams({ chapter: chapter.toString() });
    if (options.from !== undefined) params.set('from', options.from.toString());
    if (options.to !== undefined) params.set('to', options.to.toString());
    if (options.limit !== undefined) params.set('limit', options.limit.toString());
    if (options.offset !== undefined) params.set('offset', options.offset.toString());

    return this.client.get<TimelineReadModel>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/timeline-feed?${params.toString()}`,
      { signal: options.signal }
    );
  }

  public getCharacterProfile(
    seriesId: string,
    characterId: string,
    chapter: number,
    signal?: AbortSignal
  ): Promise<CharacterReadModel> {
    const params = new URLSearchParams({ chapter: chapter.toString() });
    return this.client.get<CharacterReadModel>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/characters/${encodeURIComponent(characterId)}/profile?${params.toString()}`,
      { signal }
    );
  }

  public getIntelligenceGraph(
    seriesId: string,
    chapter: number,
    graphType: 'causal' | 'relationship' = 'causal',
    signal?: AbortSignal
  ): Promise<GenericGraphReadModel> {
    const params = new URLSearchParams({
      chapter: chapter.toString(),
      graph_type: graphType,
    });
    return this.client.get<GenericGraphReadModel>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/graph?${params.toString()}`,
      { signal }
    );
  }

  public getEventNarrativeExplanation(
    seriesId: string,
    eventId: string,
    chapter: number,
    maxDepth = 4,
    signal?: AbortSignal
  ): Promise<TemporalNarrativeCausalExplanationDTO> {
    const params = new URLSearchParams({
      chapter: chapter.toString(),
      max_depth: maxDepth.toString(),
    });
    return this.client.get<TemporalNarrativeCausalExplanationDTO>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/event-narrative/${encodeURIComponent(eventId)}?${params.toString()}`,
      { signal }
    );
  }

  public getCharacterNarrativeCausality(
    seriesId: string,
    characterId: string,
    chapter: number,
    maxDepth = 4,
    signal?: AbortSignal
  ): Promise<TemporalNarrativeCausalExplanationDTO> {
    const params = new URLSearchParams({
      chapter: chapter.toString(),
      max_depth: maxDepth.toString(),
    });
    return this.client.get<TemporalNarrativeCausalExplanationDTO>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/character-narrative-causality/${encodeURIComponent(characterId)}?${params.toString()}`,
      { signal }
    );
  }

  public getCharacterArc(
    seriesId: string,
    characterId: string,
    chapter: number,
    signal?: AbortSignal
  ): Promise<CharacterArcResponse> {
    const params = new URLSearchParams({ chapter: chapter.toString() });
    return this.client.get<CharacterArcResponse>(
      `/series/${encodeURIComponent(seriesId)}/intelligence/character-arc/${encodeURIComponent(characterId)}?${params.toString()}`,
      { signal }
    );
  }

  public getTemporalComparison(
    seriesId: string,
    fromChapter: number,
    toChapter: number,
    readerChapter: number,
    signal?: AbortSignal
  ): Promise<TemporalComparisonResponse> {
    const params = new URLSearchParams({
      from_chapter: fromChapter.toString(),
      to_chapter: toChapter.toString(),
      reader_chapter: readerChapter.toString(),
    });
    return this.client.get<TemporalComparisonResponse>(
      `/series/${encodeURIComponent(seriesId)}/comparison?${params.toString()}`,
      { signal }
    );
  }
}

export const intelligenceQueries = new IntelligenceQueries();
