import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useFactionMembers } from '../hooks/useFactions';

export const FactionMembers: React.FC<{ factionId: string }> = ({ factionId }) => {
  const { seriesId, readerChapter } = useReader();
  const { data: members, isLoading, isError } = useFactionMembers(seriesId, factionId, readerChapter);

  if (isLoading) return <p>Loading membership history...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load membership history.</p>;
  if (!members || members.length === 0) return <p style={{ color: '#7f8c8d' }}>No recorded members for this faction.</p>;

  return (
    <div>
      <h3>Membership History (Chapter {readerChapter})</h3>
      <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '16px' }}>
        <thead>
          <tr style={{ backgroundColor: '#ecf0f1', textAlign: 'left' }}>
            <th style={{ padding: '12px', borderBottom: '2px solid #bdc3c7' }}>Character</th>
            <th style={{ padding: '12px', borderBottom: '2px solid #bdc3c7' }}>Status</th>
            <th style={{ padding: '12px', borderBottom: '2px solid #bdc3c7' }}>Joined Chapter</th>
            <th style={{ padding: '12px', borderBottom: '2px solid #bdc3c7' }}>Left Chapter</th>
          </tr>
        </thead>
        <tbody>
          {members.map((m, i) => (
            <tr key={`${m.character_id}-${i}`} style={{ borderBottom: '1px solid #ecf0f1' }}>
              <td style={{ padding: '12px', fontWeight: 'bold', color: '#2c3e50' }}>{m.name}</td>
              <td style={{ padding: '12px' }}>
                <span style={{ 
                  backgroundColor: m.is_active ? '#2ecc71' : '#95a5a6', 
                  color: 'white', 
                  padding: '4px 8px', 
                  borderRadius: '4px',
                  fontSize: '0.85em'
                }}>
                  {m.is_active ? 'ACTIVE' : 'FORMER'}
                </span>
              </td>
              <td style={{ padding: '12px' }}>{m.joined_chapter}</td>
              <td style={{ padding: '12px', color: '#7f8c8d' }}>{'—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
