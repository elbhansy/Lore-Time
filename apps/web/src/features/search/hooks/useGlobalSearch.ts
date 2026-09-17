import { useQuery } from '@tanstack/react-query';
import { searchApi } from '../services/search-api';
import { SearchType } from '../types';

export const useGlobalSearch = (seriesId: string, q: string, type: SearchType, chapter: number, page: number = 1, pageSize: number = 20) => {
  return useQuery({
    queryKey: ['search', seriesId, q, type, chapter, page, pageSize],
    queryFn: () => searchApi.globalSearch(seriesId, q, type, chapter, page, pageSize),
    enabled: Boolean(seriesId) && q.length > 0 && chapter > 0,
    staleTime: 60000,
  });
};

export const useSearchSuggestions = (seriesId: string, q: string, chapter: number) => {
  return useQuery({
    queryKey: ['search-suggestions', seriesId, q, chapter],
    queryFn: () => searchApi.getSuggestions(seriesId, q, chapter),
    enabled: Boolean(seriesId) && q.length >= 2 && chapter > 0,
    staleTime: 60000,
  });
};
