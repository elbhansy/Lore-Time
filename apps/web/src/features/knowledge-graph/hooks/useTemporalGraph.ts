import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../../../services/api/graph-api';

export const useTemporalGraph = (seriesId: string, chapter: number) => {
  return useQuery({
    queryKey: ['temporal-graph', seriesId, chapter],
    queryFn: () => graphApi.getTemporalGraph(seriesId, chapter),
    enabled: Boolean(seriesId) && chapter > 0,
  });
};
