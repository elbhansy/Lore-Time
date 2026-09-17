import { useQuery } from '@tanstack/react-query';
import { seriesApi } from '../../../services/api/series-api';

export const useRankProgression = (seriesId: string, characterId: string, readerChapter: number) => {
  return useQuery({
    queryKey: ['rank-progression', seriesId, characterId, readerChapter],
    queryFn: () => seriesApi.getRankProgression(seriesId, characterId, readerChapter),
    enabled: Boolean(seriesId) && Boolean(characterId) && readerChapter > 0,
  });
};
