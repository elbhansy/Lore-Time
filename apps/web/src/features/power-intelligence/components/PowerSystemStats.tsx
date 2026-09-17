import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useRankDistribution } from '../hooks/usePowerIntelligence';

export const PowerSystemStats: React.FC<{ powerSystemId: string }> = ({ powerSystemId }) => {
  const { seriesId, readerChapter } = useReader();
  const { data, isLoading, isError } = useRankDistribution(seriesId, powerSystemId, readerChapter);

  if (isLoading) return <p>Loading stats...</p>;
  if (isError || !data) return <p style={{ color: 'red' }}>Failed to load distribution.</p>;

  const maxCount = Math.max(...data.distribution.map(d => d.count), 1);

  return (
    <div style={{ marginTop: '24px', padding: '16px', border: '1px solid #ecf0f1', borderRadius: '8px' }}>
      <h3>Rank Distribution</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
        {data.distribution.map(d => (
          <div key={d.rank_id} style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '100px', fontWeight: 'bold' }}>{d.rank_name}</div>
            <div style={{ flex: 1, height: '24px', backgroundColor: '#ecf0f1', borderRadius: '4px', overflow: 'hidden' }}>
              <div style={{ 
                width: `${(d.count / maxCount) * 100}%`, 
                height: '100%', 
                backgroundColor: '#3498db',
                transition: 'width 0.3s ease'
              }} />
            </div>
            <div style={{ width: '40px', textAlign: 'right', color: '#7f8c8d' }}>{d.count}</div>
          </div>
        ))}
      </div>
    </div>
  );
};
