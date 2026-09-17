import { useQuery } from '@tanstack/react-query';
import { seriesApi } from '../../../services/api/series-api';

export const useCharacters = (seriesId: string) => {
  return useQuery({
    queryKey: ['characters', seriesId],
    queryFn: () => seriesApi.getCharacters(seriesId),
    enabled: Boolean(seriesId),
  });
};

export const useCharacterProfile = (seriesId: string, characterId: string, readerChapter: number) => {
  return useQuery({
    queryKey: ['character', seriesId, characterId, readerChapter],
    queryFn: () => seriesApi.getCharacter(seriesId, characterId, readerChapter),
    enabled: Boolean(seriesId) && Boolean(characterId) && readerChapter > 0,
  });
};
