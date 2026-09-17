import React from 'react';
import { useRelationshipHistory } from '../hooks/useRelationshipHistory';
import { useReader } from '../../reader/reader-store';

interface RelationshipDetailsProps {
  seriesId: string;
  sourceId: string;
  targetId: string;
  sourceName: string;
  targetName: string;
  onClose: () => void;
}

export const RelationshipDetails: React.FC<RelationshipDetailsProps> = ({ seriesId, sourceId, targetId, sourceName, targetName, onClose }) => {
  const { readerChapter } = useReader();
  const { data, isLoading } = useRelationshipHistory(seriesId, sourceId, targetId, readerChapter);

  return (
    <div style={{ position: 'absolute', top: 16, right: 16, width: 300, backgroundColor: 'white', border: '1px solid #ccc', borderRadius: 8, padding: 16, zIndex: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <h4 style={{ margin: 0 }}>Relationship Details</h4>
        <button onClick={onClose} style={{ cursor: 'pointer', border: 'none', background: 'none', fontSize: '1.2em' }}>×</button>
      </div>

      <div style={{ marginBottom: 16, textAlign: 'center', backgroundColor: '#f8f9fa', padding: 8, borderRadius: 4 }}>
        <strong>{sourceName}</strong> <br/>
        <span style={{ color: '#7f8c8d', fontSize: '0.9em' }}>↓</span> <br/>
        <strong>{targetName}</strong>
      </div>

      <h5 style={{ margin: '0 0 8px 0' }}>History</h5>
      {isLoading && <p>Loading history...</p>}
      {!isLoading && (!data || data.history.length === 0) && <p style={{ fontSize: '0.9em', color: '#7f8c8d' }}>No history found.</p>}
      
      {!isLoading && data && data.history.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {data.history.map((evt, idx) => (
            <div key={idx} style={{ padding: 8, border: '1px solid #eee', borderRadius: 4, display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontWeight: 'bold', color: evt.type === 'ENDED' ? '#e74c3c' : '#2980b9' }}>
                {evt.type}
              </span>
              <span style={{ fontSize: '0.9em', color: '#7f8c8d' }}>Ch. {evt.chapter}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
