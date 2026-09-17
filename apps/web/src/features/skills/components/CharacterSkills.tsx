import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useCharacterSkills } from '../hooks/useSkills';

export const CharacterSkills: React.FC<{ characterId: string }> = ({ characterId }) => {
  const { seriesId, readerChapter } = useReader();
  const { data: progression, isLoading, isError } = useCharacterSkills(seriesId, characterId, readerChapter);

  if (isLoading) return <p>Loading skills...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load skills.</p>;
  if (!progression || progression.active_skills.length === 0) return <p style={{ color: '#7f8c8d' }}>No recorded skills for this character.</p>;

  // Basic rendering of active skills
  return (
    <div>
      <h3>Active Skills</h3>
      <ul style={{ listStyleType: 'none', padding: 0 }}>
        {progression.active_skills.map((s, i) => (
          <li key={`${s.skill_id}-${i}`} style={{
            padding: '12px',
            border: '1px solid #ecf0f1',
            marginBottom: '8px',
            borderRadius: '4px',
            backgroundColor: '#fdfdfd'
          }}>
            <strong>{s.skill_name || s.skill_id}</strong>
            <span style={{ fontSize: '0.85em', color: '#7f8c8d', marginLeft: '12px' }}>
              Unlocked at Ch. {s.unlocked_at}
              {s.upgraded_at ? ` (Upgraded at Ch. ${s.upgraded_at})` : ''}
            </span>
            
            {/* Show specific evolutions if available */}
            {progression.relations
              .filter(r => r.target_skill_id === s.skill_id)
              .map(r => (
                <div key={r.id} style={{ fontSize: '0.85em', color: '#9b59b6', marginTop: '4px' }}>
                  ↳ {r.type.replace('_', ' ')} from {r.source_skill_id}
                </div>
              ))}
          </li>
        ))}
      </ul>
    </div>
  );
};
