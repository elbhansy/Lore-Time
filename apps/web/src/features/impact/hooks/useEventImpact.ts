import { useQuery } from '@tanstack/react-query';
import { impactApi } from '../../../services/api/impact-api';

export const useEventImpact = (seriesId: string, eventId: string, readerChapter: number) => {
  return useQuery({
    queryKey: ['event-impact', seriesId, eventId, readerChapter],
    queryFn: () => impactApi.getEventImpact(seriesId, eventId, readerChapter),
    enabled: Boolean(seriesId) && Boolean(eventId) && readerChapter > 0,
    staleTime: 5 * 60 * 1000, // cache for 5 minutes
  });
};
