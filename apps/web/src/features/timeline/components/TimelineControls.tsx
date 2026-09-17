import React from 'react';
import { useReader } from '../../reader/reader-store';

export const TimelineControls: React.FC<{ totalChapters: number }> = ({ totalChapters }) => {
  const { readerChapter, setReaderChapter } = useReader();

  return (
    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginBottom: '16px' }}>
      <button onClick={() => setReaderChapter(1)} disabled={readerChapter <= 1}>[|◀]</button>
      <button onClick={() => setReaderChapter(readerChapter - 1)} disabled={readerChapter <= 1}>[◀]</button>
      
      <span style={{ margin: '0 16px', fontWeight: 'bold' }}>
        Reader Chapter: {readerChapter}
      </span>
      
      <button onClick={() => setReaderChapter(readerChapter + 1)} disabled={readerChapter >= totalChapters}>[▶]</button>
      <button onClick={() => setReaderChapter(totalChapters)} disabled={readerChapter >= totalChapters}>[▶|]</button>
    </div>
  );
};
