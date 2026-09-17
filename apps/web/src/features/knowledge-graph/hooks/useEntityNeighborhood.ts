import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../../../services/api/graph-api';

export const useEntityNeighborhood = (seriesId: string, entityId: string, chapter: number, depth: number = 1) => {
  return useQuery({
    queryKey: ['entity-neighborhood', seriesId, entityId, chapter, depth],
    queryFn: () => graphApi.getEntityNeighborhood(seriesId, entityId, chapter, depth),
    enabled: Boolean(seriesId) && Boolean(entityId) && chapter > 0,
  });
};
