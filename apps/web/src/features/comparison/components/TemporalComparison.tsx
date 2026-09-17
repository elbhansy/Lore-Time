import React, { useState } from 'react';
import { useReader } from '../../reader/reader-store';
import { useTemporalComparison } from '../hooks/useTemporalComparison';
import { useCharacters } from '../../characters/hooks/useCharacters';
import { ComparisonControls } from './ComparisonControls';
import { ComparisonSummary } from './ComparisonSummary';
import { CharacterChanges } from './CharacterChanges';
import { PowerChanges } from './PowerChanges';
import { RelationshipChanges } from './RelationshipChanges';
import { SkillChanges } from './SkillChanges';
import { ImpactTimeline } from '../../impact/components/ImpactTimeline';

export const TemporalComparison: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  
  // Local state for from/to logic
  // Default to a 10 chapter gap, capped by readerChapter.
  const [toChapter, setToChapter] = useState(readerChapter);
  const [fromChapter, setFromChapter] = useState(Math.max(1, readerChapter - 10));
  const [showImpacts, setShowImpacts] = useState(false);
  
  // Enforce bounds if readerChapter dynamically shrinks
  React.useEffect(() => {
    if (toChapter > readerChapter) {
      setToChapter(readerChapter);
    }
  }, [toChapter, readerChapter]);

  React.useEffect(() => {
    if (toChapter > 1 && fromChapter >= toChapter) {
      setFromChapter(Math.max(1, toChapter - 1));
    } else if (toChapter === 1 && fromChapter !== 1) {
      setFromChapter(1);
    }
  }, [fromChapter, toChapter]);

  const { data: charData } = useCharacters(seriesId);
  const { data: compData, isLoading, isError, error } = useTemporalComparison(seriesId, fromChapter, toChapter, readerChapter);

  const getCharacterName = (id: string) => {
    if (!charData) return id;
    const char = charData.find(c => c.id === id);
    return char ? char.name : id;
  };

  return (
    <div style={{ padding: '24px 0' }}>
      <ComparisonControls 
        fromChapter={fromChapter} 
        toChapter={toChapter} 
        readerChapter={readerChapter}
        onFromChange={setFromChapter}
        onToChange={setToChapter}
      />
      
      {isError && (
        <div style={{ padding: '16px', backgroundColor: '#fdedec', color: '#c0392b', borderRadius: '4px', border: '1px solid #e74c3c' }}>
          Error: {(error as any)?.response?.data?.detail || error.message}
        </div>
      )}
      
      {isLoading && <p>Computing Temporal Comparison...</p>}
      
      {compData && (
        <div>
          <ComparisonSummary summary={compData.summary} />
          
          <CharacterChanges changes={compData.character_changes} getCharacterName={getCharacterName} />
          <PowerChanges changes={compData.power_changes} getCharacterName={getCharacterName} />
          <RelationshipChanges changes={compData.relationship_changes} getCharacterName={getCharacterName} />
          <SkillChanges changes={compData.skill_changes} getCharacterName={getCharacterName} />
          
          {compData.character_changes.length === 0 && compData.power_changes.length === 0 && 
           compData.relationship_changes.length === 0 && compData.skill_changes.length === 0 && (
            <p style={{ textAlign: 'center', color: '#7f8c8d', fontStyle: 'italic', marginTop: '32px' }}>
              No changes detected between Chapter {fromChapter} and Chapter {toChapter}.
            </p>
          )}

          <div style={{ marginTop: '32px', borderTop: '2px dashed #ccc', paddingTop: '24px' }}>
            <button 
              onClick={() => setShowImpacts(!showImpacts)}
              style={{ padding: '8px 16px', backgroundColor: '#8e44ad', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold' }}
            >
              {showImpacts ? 'Hide Related Events' : 'Show Related Events'}
            </button>
            
            {showImpacts && (
              <ImpactTimeline seriesId={seriesId} fromChapter={fromChapter} toChapter={toChapter} readerChapter={readerChapter} />
            )}
          </div>
        </div>
      )}
    </div>
  );
};
