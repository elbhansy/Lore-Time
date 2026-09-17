import React from 'react';
import { RankResponse } from '../../../types/api';

export const RankList: React.FC<{ ranks: RankResponse[] }> = ({ ranks }) => {
  if (ranks.length === 0) return <p style={{ color: '#7f8c8d' }}>No ranks discovered yet.</p>;

  // Sort by order ascending
  const sortedRanks = [...ranks].sort((a, b) => a.order - b.order);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      {sortedRanks.map(rank => (
        <div key={rank.id} style={{ padding: '8px', border: '1px solid #ddd', borderRadius: '4px' }}>
          <span style={{ fontWeight: 'bold' }}>{rank.name}</span>
          <span style={{ color: '#7f8c8d', fontSize: '0.9em', marginLeft: '8px' }}>
            (Introduced Ch. {rank.introduced_chapter})
          </span>
        </div>
      ))}
    </div>
  );
};
