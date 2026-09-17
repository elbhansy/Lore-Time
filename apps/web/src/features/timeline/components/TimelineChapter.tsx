import React from 'react';
import { TimelineChapter } from '../types';
import { EventImpactCard } from '../../impact/components/EventImpactCard';
import { useReader } from '../../reader/reader-store';

export const TimelineChapterNode: React.FC<{ chapter: TimelineChapter }> = ({ chapter }) => {
  const { seriesId, readerChapter } = useReader();
  return (
    <div style={{ marginBottom: '24px', position: 'relative' }}>
      {/* Visual vertical line connecting chapters */}
      <div style={{ 
        position: 'absolute', 
        left: '11px', 
        top: '24px', 
        bottom: '-24px', 
        width: '2px', 
        backgroundColor: '#e0e0e0',
        zIndex: -1
      }} />
      
      <div style={{ display: 'flex', alignItems: 'center', marginBottom: '8px' }}>
        <div style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          backgroundColor: chapter.isCurrent ? '#2c3e50' : '#bdc3c7',
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '12px',
          fontWeight: 'bold',
          marginRight: '12px'
        }}>
          {chapter.number}
        </div>
        <h4 style={{ margin: 0, color: chapter.isCurrent ? '#2c3e50' : '#7f8c8d' }}>
          Chapter {chapter.number} {chapter.isCurrent && '(CURRENT)'}
        </h4>
      </div>
      
      <div>
        {chapter.events.map(event => (
          <EventImpactCard key={event.id} event={event} seriesId={seriesId} readerChapter={readerChapter} />
        ))}
      </div>
    </div>
  );
};
