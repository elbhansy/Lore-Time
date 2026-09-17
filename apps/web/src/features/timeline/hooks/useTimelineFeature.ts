import { useMemo, useState } from 'react';
import { useTimeline as useTimelineQuery } from '../../world-state/queries';
import { TimelineCategory, TimelineChapter } from '../types';
import { groupEventsByChapter, filterEventsByCategory } from '../utils/timeline-utils';
import { useReader } from '../../reader/reader-store';

export const useTimelineFeature = () => {
  const { seriesId, readerChapter } = useReader();
  const [category, setCategory] = useState<TimelineCategory>('All');
  
  // Hardcoded 'from' chapter for now, could be paginated later
  const { data: rawEvents, isLoading, isError } = useTimelineQuery(seriesId, readerChapter, 1, readerChapter);

  const timelineChapters = useMemo(() => {
    if (!rawEvents) return [];
    
    // 1. Defensively group and sort
    const allGrouped = groupEventsByChapter(rawEvents, readerChapter);
    
    // 2. Filter visually
    if (category === 'All') return allGrouped;
    
    return allGrouped.map(tc => ({
      ...tc,
      events: filterEventsByCategory(tc.events, category)
    })).filter(tc => tc.events.length > 0); // Drop chapters that become empty after filter
    
  }, [rawEvents, readerChapter, category]);

  return {
    timelineChapters,
    isLoading,
    isError,
    category,
    setCategory
  };
};
