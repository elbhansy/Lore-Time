import { useQuery } from '@tanstack/react-query';
import { relationshipApi } from '../../../services/api/relationship-api';

export const useRelationshipGraph = (seriesId: string, readerChapter: number, type: string = 'ALL') => {
  return useQuery({
    queryKey: ['relationship-graph', seriesId, readerChapter, type],
    queryFn: () => relationshipApi.getGraph(seriesId, readerChapter, type),
    enabled: Boolean(seriesId) && readerChapter > 0,
  });
};
