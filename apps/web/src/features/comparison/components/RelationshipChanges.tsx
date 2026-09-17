import React from 'react';
import { RelationshipDiffDTO } from '../../../types/api';

interface RelationshipChangesProps {
  changes: RelationshipDiffDTO[];
  getCharacterName: (id: string) => string;
}

export const RelationshipChanges: React.FC<RelationshipChangesProps> = ({ changes, getCharacterName }) => {
  if (changes.length === 0) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ borderBottom: '2px solid #2ecc71', paddingBottom: '8px' }}>Relationship Changes</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
        {changes.map((change, idx) => (
          <div key={idx} style={{ padding: '12px', backgroundColor: '#fff', border: '1px solid #eee', borderRadius: '6px', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <strong>{getCharacterName(change.source_id)}</strong>
              <span style={{ color: '#bdc3c7' }}>→</span>
              <strong>{getCharacterName(change.target_id)}</strong>
            </div>
            
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', gap: '12px', justifyContent: 'flex-end' }}>
              {change.change_type === 'CREATED' && (
                <span style={{ color: '#27ae60', fontWeight: 'bold', backgroundColor: '#e9f7ef', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em' }}>
                  NEW: {change.after_type}
                </span>
              )}
              {change.change_type === 'ENDED' && (
                <span style={{ color: '#c0392b', fontWeight: 'bold', backgroundColor: '#fdedec', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em' }}>
                  ENDED: {change.before_type}
                </span>
              )}
              {change.change_type === 'CHANGED' && (
                <>
                  <span style={{ color: '#7f8c8d', fontSize: '0.9em' }}>{change.before_type}</span>
                  <span style={{ color: '#3498db', fontWeight: 'bold' }}>→</span>
                  <span style={{ color: '#2980b9', fontWeight: 'bold' }}>{change.after_type}</span>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
