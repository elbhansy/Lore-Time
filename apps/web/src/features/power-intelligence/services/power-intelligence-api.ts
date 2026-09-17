import { apiClient } from '../../../services/api/client';
import { PowerProgressionDTO, PowerSystemDistributionDTO, PowerComparisonDTO } from '../types';

export const powerIntelligenceApi = {
  getPowerProgression: (seriesId: string, characterId: string, powerSystemId: string, chapter: number): Promise<PowerProgressionDTO> => {
    return apiClient<PowerProgressionDTO>(`/series/${seriesId}/characters/${characterId}/power-progression?power_system_id=${powerSystemId}&chapter=${chapter}`);
  },
  getRankDistribution: (seriesId: string, powerSystemId: string, chapter: number): Promise<PowerSystemDistributionDTO> => {
    return apiClient<PowerSystemDistributionDTO>(`/series/${seriesId}/power-systems/${powerSystemId}/distribution?chapter=${chapter}`);
  },
  getRankPopulation: (seriesId: string, powerSystemId: string, rankId: string, chapter: number): Promise<string[]> => {
    return apiClient<string[]>(`/series/${seriesId}/power-systems/${powerSystemId}/ranks/${rankId}/characters?chapter=${chapter}`);
  },
  getPowerComparison: (seriesId: string, characterA: string, characterB: string, powerSystemId: string, chapter: number): Promise<PowerComparisonDTO> => {
    return apiClient<PowerComparisonDTO>(`/series/${seriesId}/power-comparison?character_a=${characterA}&character_b=${characterB}&power_system_id=${powerSystemId}&chapter=${chapter}`);
  }
};
