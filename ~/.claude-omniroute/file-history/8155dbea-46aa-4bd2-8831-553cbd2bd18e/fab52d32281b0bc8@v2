import { apiClient } from '../../../services/api/client';
import {
  AnalyticsOverviewDTO,
  CharacterActivityDTO,
  RelationshipAnalyticsDTO,
} from '../types';

export interface AnalyticsScope {
  from?: number;
  to?: number;
}

const buildParams = (scope: AnalyticsScope, limit?: number): string => {
  const params = new URLSearchParams();
  if (scope.from != null) params.set('from', String(scope.from));
  if (scope.to != null) params.set('to', String(scope.to));
  if (limit != null) params.set('limit', String(limit));
  const qs = params.toString();
  return qs ? `?${qs}` : '';
};

export const analyticsApi = {
  getOverview: (seriesId: string, scope: AnalyticsScope = {}): Promise<AnalyticsOverviewDTO> =>
    apiClient<AnalyticsOverviewDTO>(`/series/${seriesId}/analytics/overview${buildParams(scope)}`),

  getEntityActivity: (
    seriesId: string,
    entityId: string,
    scope: AnalyticsScope = {},
    limit: number = 50,
  ): Promise<CharacterActivityDTO[]> =>
    apiClient<CharacterActivityDTO[]>(
      `/series/${seriesId}/analytics/entities/${encodeURIComponent(entityId)}${buildParams(scope, limit)}`,
    ),

  getRelationships: (
    seriesId: string,
    scope: AnalyticsScope = {},
    limit: number = 50,
  ): Promise<RelationshipAnalyticsDTO> =>
    apiClient<RelationshipAnalyticsDTO>(
      `/series/${seriesId}/analytics/relationships${buildParams(scope, limit)}`,
    ),
};
