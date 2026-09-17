import { apiClient } from '../../../services/api/client';
import { FactionExplorerItemDTO, FactionProfileDTO, FactionMemberDTO, FactionLeadershipDTO } from '../types';
import type { EventResponse } from '../../../types/api';

export const factionApi = {
  getFactions: (seriesId: string, chapter: number): Promise<FactionExplorerItemDTO[]> => {
    return apiClient<FactionExplorerItemDTO[]>(`/series/${seriesId}/factions?chapter=${chapter}`);
  },
  getFactionProfile: (seriesId: string, factionId: string, chapter: number): Promise<FactionProfileDTO> => {
    return apiClient<FactionProfileDTO>(`/series/${seriesId}/factions/${factionId}?chapter=${chapter}`);
  },
  getFactionMembers: (seriesId: string, factionId: string, chapter: number): Promise<FactionMemberDTO[]> => {
    return apiClient<FactionMemberDTO[]>(`/series/${seriesId}/factions/${factionId}/members?chapter=${chapter}`);
  },
  getFactionLeadership: (seriesId: string, factionId: string, chapter: number): Promise<FactionLeadershipDTO[]> => {
    return apiClient<FactionLeadershipDTO[]>(`/series/${seriesId}/factions/${factionId}/leadership?chapter=${chapter}`);
  },
  getFactionTimeline: (seriesId: string, factionId: string, chapter: number): Promise<EventResponse[]> => {
    return apiClient<EventResponse[]>(`/series/${seriesId}/factions/${factionId}/timeline?chapter=${chapter}`);
  }
};
