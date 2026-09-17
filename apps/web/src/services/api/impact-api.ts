import { apiClient } from './client';
import { ImpactAnalysisResultDTO } from '../../types/api';

export const impactApi = {
  getEventImpact: (seriesId: string, eventId: string, readerChapter: number): Promise<ImpactAnalysisResultDTO> => {
    return apiClient<ImpactAnalysisResultDTO>(`/series/${seriesId}/events/${eventId}/impact?chapter=${readerChapter}`);
  },

  getImpactTimeline: (seriesId: string, fromChapter: number, toChapter: number, readerChapter: number): Promise<ImpactAnalysisResultDTO[]> => {
    return apiClient<ImpactAnalysisResultDTO[]>(`/series/${seriesId}/impact-timeline?from_chapter=${fromChapter}&to_chapter=${toChapter}&reader_chapter=${readerChapter}`);
  }
};
