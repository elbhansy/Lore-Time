import { useQuery } from '@tanstack/react-query';
import { seriesApi } from '../../services/api/series-api';

export const useWorldState = (seriesId: string, chapter: number) => {
  return useQuery({
    queryKey: ['world-state', seriesId, chapter],
    queryFn: () => seriesApi.getWorldState(seriesId, chapter),
    enabled: Boolean(seriesId),
  });
};

export const useTimeline = (seriesId: string, readerChapter: number, from: number, to: number) => {
  return useQuery({
    queryKey: ['timeline', seriesId, readerChapter, from, to],
    queryFn: () => seriesApi.getTimeline(seriesId, readerChapter, from, to),
    enabled: Boolean(seriesId),
  });
};
