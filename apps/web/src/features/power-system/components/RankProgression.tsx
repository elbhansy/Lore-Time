import React from 'react';
import { RankResponse } from '../../../types/api';

export const RankProgression: React.FC<{ ranks: RankResponse[] }> = ({ ranks }) => {
  if (ranks.length === 0) return <p style={{ fontStyle: 'italic', color: '#7f8c8d' }}>No rank changes recorded.</p>;

  // Ranks are already returned in chronological order by the backend
  return (
    <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
      {ranks.map((r, idx) => (
        <React.Fragment key={`${r.id}-${idx}`}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontWeight: 'bold', fontSize: '1.2em' }}>{r.name}</div>
          </div>
          {idx < ranks.length - 1 && <div style={{ color: '#bdc3c7' }}>→</div>}
        </React.Fragment>
      ))}
    </div>
  );
};
