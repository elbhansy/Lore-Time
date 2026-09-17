import { useQuery } from '@tanstack/react-query';
import { skillApi } from '../services/skill-api';

export const useSkills = (seriesId: string, chapter: number) => {
  return useQuery({
    queryKey: ['skills', seriesId, chapter],
    queryFn: () => skillApi.getSkills(seriesId, chapter),
    enabled: Boolean(seriesId) && chapter > 0,
  });
};

export const useCharacterSkills = (seriesId: string, characterId: string, chapter: number) => {
  return useQuery({
    queryKey: ['character-skills', seriesId, characterId, chapter],
    queryFn: () => skillApi.getCharacterSkills(seriesId, characterId, chapter),
    enabled: Boolean(seriesId) && Boolean(characterId) && chapter > 0,
  });
};

export const useSkillEvolution = (seriesId: string, skillId: string, chapter: number) => {
  return useQuery({
    queryKey: ['skill-evolution', seriesId, skillId, chapter],
    queryFn: () => skillApi.getSkillEvolution(seriesId, skillId, chapter),
    enabled: Boolean(seriesId) && Boolean(skillId) && chapter > 0,
  });
};
