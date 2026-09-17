import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useFactionLeadership } from '../hooks/useFactions';

export const FactionLeadership: React.FC<{ factionId: string }> = ({ factionId }) => {
  const { seriesId, readerChapter } = useReader();
  const { data: leadership, isLoading, isError } = useFactionLeadership(seriesId, factionId, readerChapter);

  if (isLoading) return <p>Loading leadership history...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load leadership history.</p>;
  if (!leadership || leadership.length === 0) return <p style={{ color: '#7f8c8d' }}>No recorded leadership for this faction.</p>;

  return (
    <div>
      <h3>Leadership Succession (Chapter {readerChapter})</h3>
      <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {leadership.map((l, i) => (
          <div key={`${l.leader_id}-${i}`} style={{ 
            display: 'flex', 
            padding: '16px', 
            border: l.active ? '2px solid #f39c12' : '1px solid #bdc3c7',
            borderRadius: '8px',
            backgroundColor: l.active ? '#fffbf0' : '#f9f9f9',
            alignItems: 'center',
            gap: '16px'
          }}>
            <div style={{ flex: '0 0 100px', fontWeight: 'bold', color: '#7f8c8d' }}>
              Ch. {l.started_at} {l.ended_at ? `- ${l.ended_at}` : ' - Present'}
            </div>
            <div style={{ flex: 1, fontSize: '1.2em', color: l.active ? '#d35400' : '#2c3e50', fontWeight: 'bold' }}>
              {l.leader_name}
            </div>
            {l.active && (
              <div style={{ backgroundColor: '#f39c12', color: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em', fontWeight: 'bold' }}>
                CURRENT LEADER
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
