import { useQuery } from '@tanstack/react-query';
import { relationshipApi } from '../../../services/api/relationship-api';

export const useRelationshipHistory = (seriesId: string, sourceId: string, targetId: string, readerChapter: number) => {
  return useQuery({
    queryKey: ['relationship-history', seriesId, sourceId, targetId, readerChapter],
    queryFn: () => relationshipApi.getHistory(seriesId, sourceId, targetId, readerChapter),
    enabled: Boolean(seriesId) && Boolean(sourceId) && Boolean(targetId) && readerChapter > 0,
  });
};
