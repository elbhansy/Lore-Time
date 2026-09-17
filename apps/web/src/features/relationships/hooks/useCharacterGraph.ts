import { useQuery } from '@tanstack/react-query';
import { relationshipApi } from '../../../services/api/relationship-api';

export const useCharacterGraph = (seriesId: string, characterId: string, readerChapter: number, depth: number) => {
  return useQuery({
    queryKey: ['character-graph', seriesId, characterId, readerChapter, depth],
    queryFn: () => relationshipApi.getCharacterGraph(seriesId, characterId, readerChapter, depth),
    enabled: Boolean(seriesId) && Boolean(characterId) && readerChapter > 0,
  });
};
