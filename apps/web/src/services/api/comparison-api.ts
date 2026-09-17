import { apiClient } from './client';
import { TemporalComparisonResponse } from '../../types/api';

export const comparisonApi = {
  compare: (seriesId: string, fromChapter: number, toChapter: number, readerChapter: number): Promise<TemporalComparisonResponse> => {
    return apiClient<TemporalComparisonResponse>(`/series/${seriesId}/comparison?from_chapter=${fromChapter}&to_chapter=${toChapter}&reader_chapter=${readerChapter}`);
  }
};
