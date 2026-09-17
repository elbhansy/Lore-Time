import React from 'react';
import { TimelineChapter } from '../types';
import { TimelineChapterNode } from './TimelineChapter';

export const TimelineTrack: React.FC<{ chapters: TimelineChapter[] }> = ({ chapters }) => {
  if (chapters.length === 0) {
    return <p style={{ color: '#7f8c8d', fontStyle: 'italic' }}>No events recorded up to this point.</p>;
  }

  return (
    <div style={{ marginTop: '24px' }}>
      {chapters.map(chapter => (
        <TimelineChapterNode key={chapter.number} chapter={chapter} />
      ))}
    </div>
  );
};
