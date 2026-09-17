import { useQuery } from '@tanstack/react-query';
import { powerIntelligenceApi } from '../services/power-intelligence-api';

export const usePowerProgression = (seriesId: string, characterId: string, powerSystemId: string, chapter: number) => {
  return useQuery({
    queryKey: ['power-progression', seriesId, characterId, powerSystemId, chapter],
    queryFn: () => powerIntelligenceApi.getPowerProgression(seriesId, characterId, powerSystemId, chapter),
    enabled: Boolean(seriesId) && Boolean(characterId) && Boolean(powerSystemId) && chapter > 0,
  });
};

export const useRankDistribution = (seriesId: string, powerSystemId: string, chapter: number) => {
  return useQuery({
    queryKey: ['rank-distribution', seriesId, powerSystemId, chapter],
    queryFn: () => powerIntelligenceApi.getRankDistribution(seriesId, powerSystemId, chapter),
    enabled: Boolean(seriesId) && Boolean(powerSystemId) && chapter > 0,
  });
};

export const useRankPopulation = (seriesId: string, powerSystemId: string, rankId: string, chapter: number) => {
  return useQuery({
    queryKey: ['rank-population', seriesId, powerSystemId, rankId, chapter],
    queryFn: () => powerIntelligenceApi.getRankPopulation(seriesId, powerSystemId, rankId, chapter),
    enabled: Boolean(seriesId) && Boolean(powerSystemId) && Boolean(rankId) && chapter > 0,
  });
};

export const usePowerComparison = (seriesId: string, characterA: string, characterB: string, powerSystemId: string, chapter: number) => {
  return useQuery({
    queryKey: ['power-comparison', seriesId, characterA, characterB, powerSystemId, chapter],
    queryFn: () => powerIntelligenceApi.getPowerComparison(seriesId, characterA, characterB, powerSystemId, chapter),
    enabled: Boolean(seriesId) && Boolean(characterA) && Boolean(characterB) && Boolean(powerSystemId) && chapter > 0,
  });
};
