import React, { useState } from 'react';
import { useReader } from '../../reader/reader-store';
import { useWorldState } from '../../world-state/queries';
import { useCharacters } from '../hooks/useCharacters';
import { mergeCharactersWithWorldState } from '../utils/character-utils';
import { Link } from 'react-router-dom';

export const CharacterExplorer: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const { data: wsData, isLoading: wsLoading } = useWorldState(seriesId, readerChapter);
  const { data: charsData, isLoading: charsLoading } = useCharacters(seriesId);
  const [search, setSearch] = useState('');

  if (wsLoading || charsLoading) return <p>Loading characters...</p>;
  if (!wsData || !charsData) return null;

  const visibleCharacters = mergeCharactersWithWorldState(charsData, wsData.characters, search);

  return (
    <div style={{ marginTop: '32px' }}>
      <h3>Character Explorer (As of Chapter {readerChapter})</h3>
      
      <input 
        type="text" 
        placeholder="Search character..." 
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        style={{ padding: '8px', marginBottom: '16px', width: '100%', maxWidth: '300px' }}
      />
      
      {visibleCharacters.length === 0 ? (
        <p style={{ color: '#7f8c8d' }}>No characters found at this point in the timeline.</p>
      ) : (
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
          {visibleCharacters.map(char => (
            <Link 
              key={char.id} 
              to={`/series/${seriesId}/characters/${char.id}?chapter=${readerChapter}`}
              style={{ textDecoration: 'none', color: 'inherit' }}
            >
              <div style={{ 
                border: '1px solid #ccc', 
                borderRadius: '8px', 
                padding: '16px',
                width: '150px',
                cursor: 'pointer',
                backgroundColor: char.state.alive ? '#fff' : '#f8d7da'
              }}>
                <h4 style={{ margin: '0 0 8px 0' }}>{char.name}</h4>
                <p style={{ margin: 0, fontSize: '0.9em' }}>Rank: {char.state.rank || 'None'}</p>
                {!char.state.alive && <p style={{ margin: '4px 0 0 0', color: '#c0392b', fontWeight: 'bold' }}>DEAD</p>}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
};
