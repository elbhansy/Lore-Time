import React from 'react';
import { CharacterStateResponse } from '../../../types/api';

export const CharacterHeader: React.FC<{ name: string, state: CharacterStateResponse, readerChapter: number }> = ({ name, state, readerChapter }) => {
  return (
    <div style={{ padding: '24px', backgroundColor: state.alive ? '#e8f4f8' : '#f8d7da', borderRadius: '8px', marginBottom: '24px' }}>
      <h2 style={{ margin: '0 0 8px 0' }}>{name}</h2>
      <p style={{ margin: 0, fontStyle: 'italic', color: '#7f8c8d' }}>As of Chapter {readerChapter}</p>
      
      <div style={{ display: 'flex', gap: '24px', marginTop: '16px' }}>
        <div>
          <strong>Status:</strong> <span style={{ color: state.alive ? '#27ae60' : '#c0392b' }}>{state.alive ? 'ALIVE' : 'DEAD'}</span>
        </div>
        <div>
          <strong>Rank:</strong> {state.rank || 'Unranked'}
        </div>
        <div>
          <strong>Faction:</strong> {state.faction_id || 'None'}
        </div>
      </div>
    </div>
  );
};
