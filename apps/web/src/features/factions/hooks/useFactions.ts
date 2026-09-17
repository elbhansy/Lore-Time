import { useQuery } from '@tanstack/react-query';
import { factionApi } from '../services/faction-api';

export const useFactions = (seriesId: string, chapter: number) => {
  return useQuery({
    queryKey: ['factions', seriesId, chapter],
    queryFn: () => factionApi.getFactions(seriesId, chapter),
    enabled: Boolean(seriesId) && chapter > 0,
  });
};

export const useFaction = (seriesId: string, factionId: string, chapter: number) => {
  return useQuery({
    queryKey: ['faction', seriesId, factionId, chapter],
    queryFn: () => factionApi.getFactionProfile(seriesId, factionId, chapter),
    enabled: Boolean(seriesId) && Boolean(factionId) && chapter > 0,
  });
};

export const useFactionMembers = (seriesId: string, factionId: string, chapter: number) => {
  return useQuery({
    queryKey: ['faction-members', seriesId, factionId, chapter],
    queryFn: () => factionApi.getFactionMembers(seriesId, factionId, chapter),
    enabled: Boolean(seriesId) && Boolean(factionId) && chapter > 0,
  });
};

export const useFactionLeadership = (seriesId: string, factionId: string, chapter: number) => {
  return useQuery({
    queryKey: ['faction-leadership', seriesId, factionId, chapter],
    queryFn: () => factionApi.getFactionLeadership(seriesId, factionId, chapter),
    enabled: Boolean(seriesId) && Boolean(factionId) && chapter > 0,
  });
};

export const useFactionTimeline = (seriesId: string, factionId: string, chapter: number) => {
  return useQuery({
    queryKey: ['faction-timeline', seriesId, factionId, chapter],
    queryFn: () => factionApi.getFactionTimeline(seriesId, factionId, chapter),
    enabled: Boolean(seriesId) && Boolean(factionId) && chapter > 0,
  });
};
