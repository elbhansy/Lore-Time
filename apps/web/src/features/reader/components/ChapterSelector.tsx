import React from 'react';
import { useReader } from '../reader-store';

interface ChapterSelectorProps {
  totalChapters: number;
}

export const ChapterSelector: React.FC<ChapterSelectorProps> = ({ totalChapters }) => {
  const { readerChapter, setReaderChapter } = useReader();

  const handleDecrement = () => {
    if (readerChapter > 1) {
      setReaderChapter(readerChapter - 1);
    }
  };

  const handleIncrement = () => {
    if (readerChapter < totalChapters) {
      setReaderChapter(readerChapter + 1);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseInt(e.target.value, 10);
    if (!isNaN(val)) {
      // Bound the input between 1 and totalChapters
      const bounded = Math.max(1, Math.min(val, totalChapters));
      setReaderChapter(bounded);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', padding: '16px', borderRadius: '8px', maxWidth: '400px' }}>
      <h3>Reader Progress</h3>
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '16px' }}>
        <button onClick={handleDecrement} disabled={readerChapter <= 1}>[-]</button>
        <input 
          type="number" 
          value={readerChapter} 
          onChange={handleInputChange} 
          min={1} 
          max={totalChapters}
          style={{ width: '60px', textAlign: 'center' }}
        />
        <button onClick={handleIncrement} disabled={readerChapter >= totalChapters}>[+]</button>
      </div>
      <div>
        <progress value={readerChapter} max={totalChapters} style={{ width: '100%' }} />
      </div>
      <div style={{ textAlign: 'center', marginTop: '8px' }}>
        Chapter {readerChapter} / {totalChapters}
      </div>
    </div>
  );
};
