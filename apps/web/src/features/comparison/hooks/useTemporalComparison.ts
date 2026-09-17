import { useQuery } from '@tanstack/react-query';
import { comparisonApi } from '../../../services/api/comparison-api';

export const useTemporalComparison = (seriesId: string, fromChapter: number, toChapter: number, readerChapter: number) => {
  return useQuery({
    queryKey: ['temporal-comparison', seriesId, fromChapter, toChapter, readerChapter],
    queryFn: () => comparisonApi.compare(seriesId, fromChapter, toChapter, readerChapter),
    enabled: Boolean(seriesId) && fromChapter > 0 && toChapter > fromChapter && toChapter <= readerChapter,
    retry: false // Do not retry if we hit the 400 spoiler firewall
  });
};
