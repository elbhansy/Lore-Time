import { apiClient } from './client';
import { TemporalGraphDTO } from '../../types/api';

export const graphApi = {
  getTemporalGraph: (seriesId: string, chapter: number): Promise<TemporalGraphDTO> => {
    return apiClient<TemporalGraphDTO>(`/series/${seriesId}/graph?chapter=${chapter}`);
  },

  getEntityNeighborhood: (seriesId: string, entityId: string, chapter: number, depth: number = 1): Promise<TemporalGraphDTO> => {
    return apiClient<TemporalGraphDTO>(`/series/${seriesId}/entities/${entityId}/neighborhood?chapter=${chapter}&depth=${depth}`);
  }
};
