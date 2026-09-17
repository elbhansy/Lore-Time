import { useQuery } from '@tanstack/react-query';
import { impactApi } from '../../../services/api/impact-api';

export const useImpactTimeline = (seriesId: string, fromChapter: number, toChapter: number, readerChapter: number) => {
  return useQuery({
    queryKey: ['impact-timeline', seriesId, fromChapter, toChapter, readerChapter],
    queryFn: () => impactApi.getImpactTimeline(seriesId, fromChapter, toChapter, readerChapter),
    enabled: Boolean(seriesId) && fromChapter > 0 && toChapter >= fromChapter && readerChapter > 0,
  });
};
