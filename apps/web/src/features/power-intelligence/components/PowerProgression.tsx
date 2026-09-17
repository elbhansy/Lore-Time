import React from 'react';
import { useReader } from '../../reader/reader-store';
import { usePowerProgression } from '../hooks/usePowerIntelligence';

export const PowerProgression: React.FC<{ characterId: string }> = ({ characterId }) => {
  const { seriesId, readerChapter } = useReader();
  // Assume a default power system for now, or this could be selected
  const powerSystemId = 'cultivation'; 
  const { data, isLoading, isError } = usePowerProgression(seriesId, characterId, powerSystemId, readerChapter);

  if (isLoading) return <p>Loading progression...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load power progression.</p>;
  if (!data) return <p style={{ color: '#7f8c8d' }}>No progression data available.</p>;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3>Current Rank: <span style={{ color: '#e67e22' }}>{data.current_rank?.name || 'Unranked'}</span></h3>
        <span style={{ fontSize: '0.9em', color: '#7f8c8d' }}>System: {powerSystemId}</span>
      </div>

      <div style={{ marginTop: '24px' }}>
        <h4>Progression History & Breakthroughs</h4>
        {data.transitions.length === 0 ? (
          <p style={{ color: '#7f8c8d', fontStyle: 'italic' }}>No known transitions.</p>
        ) : (
          <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '16px', marginTop: '16px' }}>
            {data.transitions.map((t, index) => (
              <React.Fragment key={t.event_id}>
                {index === 0 && t.from_rank_id && (
                  <div style={{ padding: '8px 16px', border: '1px solid #bdc3c7', borderRadius: '4px', backgroundColor: '#ecf0f1' }}>
                    {t.from_rank_name || t.from_rank_id}
                  </div>
                )}
                
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', color: t.breakthrough_status === 'BREAKTHROUGH' ? '#27ae60' : t.breakthrough_status === 'REGRESSION' ? '#c0392b' : '#7f8c8d' }}>
                  <span style={{ fontSize: '0.8em' }}>Ch. {t.chapter}</span>
                  <span>{t.breakthrough_status === 'BREAKTHROUGH' ? '→' : t.breakthrough_status === 'REGRESSION' ? '←' : '→'}</span>
                </div>
                
                <div style={{ padding: '8px 16px', border: t.breakthrough_status === 'BREAKTHROUGH' ? '2px solid #27ae60' : '1px solid #bdc3c7', borderRadius: '4px', backgroundColor: t.breakthrough_status === 'BREAKTHROUGH' ? '#eafaf1' : '#ecf0f1', fontWeight: 'bold' }}>
                  {t.to_rank_name || t.to_rank_id}
                </div>
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
