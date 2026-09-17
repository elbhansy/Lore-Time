import { apiClient } from '../../../services/api/client';
import { SearchPageDTO, SearchSuggestionDTO, SearchType } from '../types';

export const searchApi = {
  globalSearch: (seriesId: string, q: string, type: SearchType, chapter: number, page: number, pageSize: number): Promise<SearchPageDTO> => {
    return apiClient<SearchPageDTO>(`/series/${seriesId}/search?q=${encodeURIComponent(q)}&type=${type}&chapter=${chapter}&page=${page}&page_size=${pageSize}`);
  },
  getSuggestions: (seriesId: string, q: string, chapter: number): Promise<SearchSuggestionDTO[]> => {
    return apiClient<SearchSuggestionDTO[]>(`/series/${seriesId}/search/suggestions?q=${encodeURIComponent(q)}&chapter=${chapter}`);
  }
};
