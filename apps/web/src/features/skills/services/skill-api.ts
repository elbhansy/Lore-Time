import { apiClient } from '../../../services/api/client';
import { SkillExplorerItemDTO, SkillProgressionDTO, SkillEvolutionDTO } from '../types';

export const skillApi = {
  getSkills: (seriesId: string, chapter: number): Promise<SkillExplorerItemDTO[]> => {
    return apiClient<SkillExplorerItemDTO[]>(`/series/${seriesId}/skills?chapter=${chapter}`);
  },
  getCharacterSkills: (seriesId: string, characterId: string, chapter: number): Promise<SkillProgressionDTO> => {
    return apiClient<SkillProgressionDTO>(`/series/${seriesId}/characters/${characterId}/skills?chapter=${chapter}`);
  },
  getSkillEvolution: (seriesId: string, skillId: string, chapter: number): Promise<SkillEvolutionDTO> => {
    return apiClient<SkillEvolutionDTO>(`/series/${seriesId}/skills/${skillId}/evolution?chapter=${chapter}`);
  }
};
