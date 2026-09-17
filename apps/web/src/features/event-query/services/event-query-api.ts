import { apiClient } from '../../../services/api/client';
import { EventQueryResultDTO } from '../types';

export interface EventQueryParams {
  seriesId: string;
  readerChapter: number;
  fromChapter?: number;
  toChapter?: number;
  type?: string;
  subjectId?: string;
  targetId?: string;
  page?: number;
  pageSize?: number;
}

export const eventQueryApi = {
  queryEvents: (params: EventQueryParams): Promise<EventQueryResultDTO> => {
    let url = `/series/${params.seriesId}/events?reader_chapter=${params.readerChapter}`;
    if (params.fromChapter) url += `&from_chapter=${params.fromChapter}`;
    if (params.toChapter) url += `&to_chapter=${params.toChapter}`;
    if (params.type) url += `&type=${params.type}`;
    if (params.subjectId) url += `&subject_id=${params.subjectId}`;
    if (params.targetId) url += `&target_id=${params.targetId}`;
    if (params.page) url += `&page=${params.page}`;
    if (params.pageSize) url += `&page_size=${params.pageSize}`;
    
    return apiClient<EventQueryResultDTO>(url);
  }
};
