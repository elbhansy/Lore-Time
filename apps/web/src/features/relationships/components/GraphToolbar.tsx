import React from 'react';

interface GraphToolbarProps {
  depth: number;
  onDepthChange: (d: number) => void;
  typeFilter: string;
  onTypeFilterChange: (t: string) => void;
  rootName: string;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({ depth, onDepthChange, typeFilter, onTypeFilterChange, rootName }) => {
  const types = ['ALL', 'ALLY', 'ENEMY', 'FRIEND', 'RIVAL', 'FAMILY', 'MASTER', 'DISCIPLE'];

  return (
    <div style={{ position: 'absolute', top: 16, left: 16, backgroundColor: 'rgba(255,255,255,0.95)', border: '1px solid #ddd', borderRadius: 8, padding: 12, zIndex: 10, display: 'flex', flexDirection: 'column', gap: 12, boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
      <div style={{ fontWeight: 'bold' }}>Character: {rootName}</div>
      
      <div>
        <label style={{ display: 'block', fontSize: '0.9em', marginBottom: 4, color: '#555' }}>Depth</label>
        <div style={{ display: 'flex', gap: 8 }}>
          <button 
            onClick={() => onDepthChange(1)} 
            style={{ padding: '4px 12px', border: '1px solid #3498db', backgroundColor: depth === 1 ? '#3498db' : 'white', color: depth === 1 ? 'white' : '#3498db', borderRadius: 4, cursor: 'pointer' }}
          >
            1-Hop
          </button>
          <button 
            onClick={() => onDepthChange(2)} 
            style={{ padding: '4px 12px', border: '1px solid #3498db', backgroundColor: depth === 2 ? '#3498db' : 'white', color: depth === 2 ? 'white' : '#3498db', borderRadius: 4, cursor: 'pointer' }}
          >
            2-Hop
          </button>
        </div>
      </div>

      <div>
        <label style={{ display: 'block', fontSize: '0.9em', marginBottom: 4, color: '#555' }}>Filter Relationships</label>
        <select 
          value={typeFilter} 
          onChange={(e) => onTypeFilterChange(e.target.value)}
          style={{ width: '100%', padding: 4, borderRadius: 4, border: '1px solid #ccc' }}
        >
          {types.map(t => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>
    </div>
  );
};
