import React from 'react';
import { useEventImpact } from '../hooks/useEventImpact';
import { useCharacters } from '../../characters/hooks/useCharacters';
import { EventImpactDTO } from '../../../types/api';

interface EventImpactDetailsProps {
  seriesId: string;
  eventId: string;
  readerChapter: number;
}

export const EventImpactDetails: React.FC<EventImpactDetailsProps> = ({ seriesId, eventId, readerChapter }) => {
  const { data: charData } = useCharacters(seriesId);
  const { data: impactData, isLoading, isError } = useEventImpact(seriesId, eventId, readerChapter);

  const resolveEntityName = (entityId: string) => {
    if (!charData) return entityId;
    
    // For simple character IDs
    const char = charData.find(c => c.id === entityId);
    if (char) return char.name;
    
    // For relationships like "A->B"
    if (entityId.includes('->')) {
      const parts = entityId.split('->');
      const name1 = charData.find(c => c.id === parts[0])?.name || parts[0];
      const name2 = charData.find(c => c.id === parts[1])?.name || parts[1];
      return `${name1} ↔ ${name2}`;
    }
    
    return entityId;
  };

  const renderImpactText = (impact: EventImpactDTO) => {
    const entityName = resolveEntityName(impact.affected_entity_id);
    
    if (impact.description_key === 'CHARACTER_INTRODUCED') return `${entityName} was introduced`;
    if (impact.description_key === 'CHARACTER_REMOVED') return `${entityName} died or left`;
    if (impact.description_key === 'CHARACTER_CHANGED') return `${entityName} status changed to ${impact.details?.after}`;
    if (impact.description_key === 'POWER_CHANGED') return `${entityName} advanced to Rank ${impact.details?.after}`;
    if (impact.description_key === 'RELATIONSHIP_CREATED') return `Relationship created: ${entityName} (${impact.details?.after})`;
    if (impact.description_key === 'RELATIONSHIP_ENDED') return `Relationship ended: ${entityName}`;
    if (impact.description_key === 'RELATIONSHIP_CHANGED') return `Relationship changed: ${entityName} (${impact.details?.before} → ${impact.details?.after})`;
    if (impact.description_key === 'SKILLS_UNLOCKED') return `${entityName} unlocked skills: ${impact.details?.unlocked?.join(', ')}`;
    
    return `${entityName}: ${impact.description_key}`;
  };

  if (isLoading) return <div style={{ padding: '8px', fontStyle: 'italic', color: '#7f8c8d' }}>Analyzing impacts...</div>;
  if (isError) return <div style={{ padding: '8px', color: '#e74c3c' }}>Failed to analyze impacts.</div>;
  if (!impactData || impactData.impacts.length === 0) return <div style={{ padding: '8px', fontStyle: 'italic', color: '#7f8c8d' }}>No measurable state changes from this event.</div>;

  return (
    <div style={{ marginTop: '12px', padding: '12px', backgroundColor: '#fdfefe', borderLeft: '3px solid #9b59b6', borderRadius: '4px' }}>
      <div style={{ fontSize: '0.85em', fontWeight: 'bold', color: '#9b59b6', marginBottom: '8px' }}>IMPACTS</div>
      <ul style={{ margin: 0, paddingLeft: '20px', listStyleType: 'circle', color: '#34495e', fontSize: '0.9em' }}>
        {impactData.impacts.map((impact, idx) => (
          <li key={idx} style={{ marginBottom: '4px' }}>
            {renderImpactText(impact)}
          </li>
        ))}
      </ul>
    </div>
  );
};
