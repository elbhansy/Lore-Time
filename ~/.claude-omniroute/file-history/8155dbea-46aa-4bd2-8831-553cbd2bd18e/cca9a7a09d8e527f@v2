import { useQuery } from '@tanstack/react-query';
import { analyticsApi, AnalyticsScope } from '../services/analytics-api';

export const useAnalyticsOverview = (seriesId: string, scope: AnalyticsScope = {}) =>
  useQuery({
    queryKey: ['analytics', 'overview', seriesId, scope.from ?? null, scope.to ?? null],
    queryFn: () => analyticsApi.getOverview(seriesId, scope),
    enabled: Boolean(seriesId),
    staleTime: 60000,
  });

export const useEntityActivity = (
  seriesId: string,
  entityId: string,
  scope: AnalyticsScope = {},
) =>
  useQuery({
    queryKey: ['analytics', 'entity', seriesId, entityId, scope.from ?? null, scope.to ?? null],
    queryFn: () => analyticsApi.getEntityActivity(seriesId, entityId, scope),
    enabled: Boolean(seriesId) && Boolean(entityId),
    staleTime: 60000,
  });

export const useRelationshipStats = (seriesId: string, scope: AnalyticsScope = {}) =>
  useQuery({
    queryKey: ['analytics', 'relationships', seriesId, scope.from ?? null, scope.to ?? null],
    queryFn: () => analyticsApi.getRelationships(seriesId, scope),
    enabled: Boolean(seriesId),
    staleTime: 60000,
  });
