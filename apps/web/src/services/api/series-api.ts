import { apiClient } from './client';
import type { WorldStateResponse, CharacterResponse, EventResponse, PowerSystemResponse, RankResponse } from '../../types/api';

export const seriesApi = {
  getWorldState: (seriesId: string, chapter: number): Promise<WorldStateResponse> => {
    return apiClient<WorldStateResponse>(`/series/${seriesId}/world-state?chapter=${chapter}`);
  },
  
  getCharacter: (seriesId: string, characterId: string, chapter: number): Promise<CharacterResponse> => {
    return apiClient<CharacterResponse>(`/series/${seriesId}/characters/${characterId}?chapter=${chapter}`);
  },
  
  getTimeline: (seriesId: string, readerChapter: number, from: number, to: number): Promise<EventResponse[]> => {
    return apiClient<EventResponse[]>(`/series/${seriesId}/timeline?reader_chapter=${readerChapter}&from=${from}&to=${to}`);
  },

  getCharacters: (seriesId: string): Promise<CharacterResponse[]> => {
    return apiClient<CharacterResponse[]>(`/series/${seriesId}/characters`);
  },

  getPowerSystems: (seriesId: string): Promise<PowerSystemResponse[]> => {
    return apiClient<PowerSystemResponse[]>(`/series/${seriesId}/power-systems`);
  },

  getRanks: (seriesId: string, powerSystemId: string, readerChapter: number): Promise<RankResponse[]> => {
    return apiClient<RankResponse[]>(`/series/${seriesId}/power-systems/${powerSystemId}/ranks?chapter=${readerChapter}`);
  },

  getRankProgression: (seriesId: string, characterId: string, readerChapter: number): Promise<RankResponse[]> => {
    return apiClient<RankResponse[]>(`/series/${seriesId}/characters/${characterId}/power-progression?chapter=${readerChapter}`);
  }
};
