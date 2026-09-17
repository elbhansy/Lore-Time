import React from 'react';
import { CharacterDiffDTO } from '../../../types/api';

interface CharacterChangesProps {
  changes: CharacterDiffDTO[];
  getCharacterName: (id: string) => string;
}

export const CharacterChanges: React.FC<CharacterChangesProps> = ({ changes, getCharacterName }) => {
  if (changes.length === 0) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ borderBottom: '2px solid #3498db', paddingBottom: '8px' }}>Character Changes</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '12px', marginTop: '16px' }}>
        {changes.map(change => (
          <div key={change.character_id} style={{ 
            padding: '12px', 
            borderRadius: '6px', 
            backgroundColor: change.change_type === 'INTRODUCED' ? '#e8f6f3' : change.change_type === 'REMOVED' ? '#fdf2e9' : '#f4f6f7',
            borderLeft: `4px solid ${change.change_type === 'INTRODUCED' ? '#1abc9c' : change.change_type === 'REMOVED' ? '#e67e22' : '#bdc3c7'}`
          }}>
            <div style={{ fontWeight: 'bold' }}>{getCharacterName(change.character_id)}</div>
            <div style={{ fontSize: '0.85em', marginTop: '4px', color: '#555' }}>
              {change.change_type === 'INTRODUCED' && <span>Introduced</span>}
              {change.change_type === 'REMOVED' && <span>Removed (was {change.before_status})</span>}
              {change.change_type === 'CHANGED' && <span>Status: {change.before_status} → {change.after_status}</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
