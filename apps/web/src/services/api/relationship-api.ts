import { apiClient } from './client';
import { RelationshipGraphResponse, CharacterGraphResponse, RelationshipHistoryResponse } from '../../types/api';

export const relationshipApi = {
  getGraph: (seriesId: string, readerChapter: number, type: string = 'ALL'): Promise<RelationshipGraphResponse> => {
    return apiClient<RelationshipGraphResponse>(`/series/${seriesId}/relationship-graph?chapter=${readerChapter}&type=${type}`);
  },

  getCharacterGraph: (seriesId: string, characterId: string, readerChapter: number, depth: number): Promise<CharacterGraphResponse> => {
    return apiClient<CharacterGraphResponse>(`/series/${seriesId}/characters/${characterId}/relationship-graph?chapter=${readerChapter}&depth=${depth}`);
  },

  getHistory: (seriesId: string, sourceId: string, targetId: string, readerChapter: number): Promise<RelationshipHistoryResponse> => {
    return apiClient<RelationshipHistoryResponse>(`/series/${seriesId}/relationships/${sourceId}/${targetId}/history?chapter=${readerChapter}`);
  }
};
