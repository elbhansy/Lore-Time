import React from 'react';
import { PowerDiffDTO } from '../../../types/api';

interface PowerChangesProps {
  changes: PowerDiffDTO[];
  getCharacterName: (id: string) => string;
}

export const PowerChanges: React.FC<PowerChangesProps> = ({ changes, getCharacterName }) => {
  if (changes.length === 0) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ borderBottom: '2px solid #e67e22', paddingBottom: '8px' }}>Power Changes</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '16px' }}>
        {changes.map(change => (
          <div key={change.character_id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px', backgroundColor: '#fff', border: '1px solid #eee', borderRadius: '6px' }}>
            <div style={{ fontWeight: 'bold', width: '200px' }}>{getCharacterName(change.character_id)}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
              <span style={{ color: '#7f8c8d' }}>{change.before_rank || 'None'}</span>
              <span style={{ color: '#e67e22', fontWeight: 'bold' }}>→</span>
              <span style={{ color: '#2c3e50', fontWeight: 'bold' }}>{change.after_rank || 'None'}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
