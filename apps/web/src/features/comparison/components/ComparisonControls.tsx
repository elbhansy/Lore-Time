import React from 'react';

interface ComparisonControlsProps {
  fromChapter: number;
  toChapter: number;
  readerChapter: number;
  onFromChange: (val: number) => void;
  onToChange: (val: number) => void;
}

export const ComparisonControls: React.FC<ComparisonControlsProps> = ({ fromChapter, toChapter, readerChapter, onFromChange, onToChange }) => {
  return (
    <div style={{ padding: '24px', backgroundColor: '#f8f9fa', borderRadius: '8px', border: '1px solid #ddd', marginBottom: '32px', display: 'flex', gap: '32px', alignItems: 'center' }}>
      <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>Compare From Chapter</label>
        <input 
          type="number" 
          min="1" 
          max={toChapter - 1} 
          value={fromChapter} 
          onChange={(e) => onFromChange(Math.max(1, parseInt(e.target.value) || 1))}
          style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
      </div>
      
      <div style={{ fontSize: '2em', color: '#bdc3c7' }}>→</div>
      
      <div style={{ flex: 1 }}>
        <label style={{ display: 'block', fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>To Chapter</label>
        <input 
          type="number" 
          min={fromChapter + 1} 
          max={readerChapter} 
          value={toChapter} 
          onChange={(e) => onToChange(Math.min(readerChapter, Math.max(fromChapter + 1, parseInt(e.target.value) || fromChapter + 1)))}
          style={{ width: '100%', padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
        <div style={{ fontSize: '0.8em', color: '#7f8c8d' }}>Current Reader Chapter</div>
        <div style={{ fontWeight: 'bold', textAlign: 'center', fontSize: '1.2em', color: '#2c3e50' }}>{readerChapter}</div>
      </div>
    </div>
  );
};
