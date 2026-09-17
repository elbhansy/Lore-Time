import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useReader } from '../../reader/reader-store';
import { useCharacterProfile } from '../hooks/useCharacters';
import { CharacterHeader } from './CharacterHeader';
import { CharacterPowerProgression } from './CharacterPowerProgression';
import { CharacterTimeline } from './CharacterTimeline';
import { CharacterGraph } from '../../relationships/components/CharacterGraph';
import { CharacterSkills } from '../../skills/components/CharacterSkills';

type TabType = 'overview' | 'power' | 'skills' | 'relationships' | 'timeline';

export const CharacterProfile: React.FC = () => {
  const { seriesId, characterId } = useParams<{ seriesId: string, characterId: string }>();
  const { readerChapter } = useReader();
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  
  const activeSeriesId = seriesId || '';
  const activeCharId = characterId || '';
  const { data: charData, isLoading, isError } = useCharacterProfile(activeSeriesId, activeCharId, readerChapter);

  if (!seriesId || !characterId) return <p>Invalid route.</p>;

  if (isLoading) return <p>Loading character profile...</p>;
  if (isError || !charData) return <p style={{ color: 'red' }}>Character not found or not yet introduced by this chapter.</p>;
  
  // Spoiler Firewall: Block if state indicates they do not exist
  if (!charData.state.exists) {
    return (
      <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
        <Link to={`/series/${seriesId}`}>&larr; Back to Series</Link>
        <p style={{ color: 'red', marginTop: '24px' }}>
          This character has not been introduced as of Chapter {readerChapter}.
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '24px' }}>
      <Link to={`/series/${seriesId}`}>&larr; Back to Series</Link>
      
      <div style={{ marginTop: '24px' }}>
        <CharacterHeader name={charData.name} state={charData.state} readerChapter={readerChapter} />
        
        <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid #bdc3c7', paddingBottom: '8px', marginBottom: '24px' }}>
          {['overview', 'power', 'skills', 'relationships', 'timeline'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab as TabType)}
              style={{
                padding: '8px 16px',
                backgroundColor: activeTab === tab ? '#3498db' : 'transparent',
                color: activeTab === tab ? 'white' : '#7f8c8d',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: activeTab === tab ? 'bold' : 'normal',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>

        <div>
          {activeTab === 'overview' && (
            <div>
              <h3>Character Overview</h3>
              <p>Select a tab to explore.</p>
            </div>
          )}
          {activeTab === 'power' && <CharacterPowerProgression seriesId={seriesId} characterId={characterId} readerChapter={readerChapter} />}
          {activeTab === 'skills' && <CharacterSkills characterId={characterId} />}
          {activeTab === 'relationships' && <CharacterGraph seriesId={seriesId} characterId={characterId} />}
          {activeTab === 'timeline' && <CharacterTimeline seriesId={seriesId} characterId={characterId} readerChapter={readerChapter} />}
        </div>
        
      </div>
    </div>
  );
};
