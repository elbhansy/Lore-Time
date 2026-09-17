import React from 'react';
import { SkillDiffDTO } from '../../../types/api';

interface SkillChangesProps {
  changes: SkillDiffDTO[];
  getCharacterName: (id: string) => string;
}

export const SkillChanges: React.FC<SkillChangesProps> = ({ changes, getCharacterName }) => {
  if (changes.length === 0) return null;

  return (
    <div style={{ marginBottom: '24px' }}>
      <h3 style={{ borderBottom: '2px solid #9b59b6', paddingBottom: '8px' }}>Skill Unlocks</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px', marginTop: '16px' }}>
        {changes.map(change => (
          <div key={change.character_id} style={{ padding: '16px', backgroundColor: '#f9ebfb', border: '1px solid #e1bce9', borderRadius: '8px' }}>
            <div style={{ fontWeight: 'bold', color: '#8e44ad', marginBottom: '8px' }}>{getCharacterName(change.character_id)}</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
              {change.unlocked_skills.map(skill => (
                <span key={skill} style={{ backgroundColor: 'white', padding: '4px 8px', borderRadius: '4px', fontSize: '0.85em', color: '#555', border: '1px solid #ddd' }}>
                  ⭐ {skill}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
