import React, { useMemo } from 'react';
import { useTimeline } from '../../world-state/queries';
import { TimelineChapterNode } from '../../timeline/components/TimelineChapter';
import { groupEventsByChapter } from '../../timeline/utils/timeline-utils';

export const CharacterTimeline: React.FC<{ seriesId: string, characterId: string, readerChapter: number }> = ({ seriesId, characterId, readerChapter }) => {
  const { data: rawEvents, isLoading } = useTimeline(seriesId, readerChapter, 1, readerChapter);

  const charTimelineChapters = useMemo(() => {
    if (!rawEvents) return [];
    
    // Filter to events where this character is subject or target
    const charEvents = rawEvents.filter(e => 
      e.subject_id === characterId || e.target_id === characterId
    );
    
    return groupEventsByChapter(charEvents, readerChapter);
  }, [rawEvents, characterId, readerChapter]);

  if (isLoading) return <p>Loading character timeline...</p>;
  if (charTimelineChapters.length === 0) return <p>No events found for this character.</p>;

  return (
    <div style={{ marginTop: '32px' }}>
      <h3>Character Timeline</h3>
      {charTimelineChapters.map(tc => (
        <TimelineChapterNode key={tc.number} chapter={tc} />
      ))}
    </div>
  );
};
