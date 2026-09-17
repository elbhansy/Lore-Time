import { useQuery } from '@tanstack/react-query';
import { eventQueryApi, EventQueryParams } from '../services/event-query-api';

export const useEventQuery = (params: EventQueryParams) => {
  return useQuery({
    queryKey: ['events', params],
    queryFn: () => eventQueryApi.queryEvents(params),
    enabled: Boolean(params.seriesId) && params.readerChapter > 0,
    staleTime: 60000,
  });
};
