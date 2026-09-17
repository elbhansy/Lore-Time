import { useQuery } from '@tanstack/react-query';
import { seriesApi } from '../../../services/api/series-api';

export const usePowerSystems = (seriesId: string) => {
  return useQuery({
    queryKey: ['power-systems', seriesId],
    queryFn: () => seriesApi.getPowerSystems(seriesId),
    enabled: Boolean(seriesId),
  });
};

export const useRanks = (seriesId: string, powerSystemId: string, readerChapter: number) => {
  return useQuery({
    queryKey: ['ranks', seriesId, powerSystemId, readerChapter],
    queryFn: () => seriesApi.getRanks(seriesId, powerSystemId, readerChapter),
    enabled: Boolean(seriesId) && Boolean(powerSystemId) && readerChapter > 0,
  });
};
