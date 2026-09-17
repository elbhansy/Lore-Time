import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useSkills } from '../hooks/useSkills';

export const SkillExplorer: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const { data: skills, isLoading, isError } = useSkills(seriesId, readerChapter);

  if (isLoading) return <p>Loading skills...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load skills.</p>;
  if (!skills || skills.length === 0) return <p style={{ color: '#7f8c8d' }}>No skills revealed up to Chapter {readerChapter}.</p>;

  return (
    <div style={{ marginTop: '24px' }}>
      <h3>Skill & Ability Explorer</h3>
      <p style={{ color: '#7f8c8d' }}>Showing all skills revealed up to Chapter {readerChapter}</p>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px', marginTop: '16px' }}>
        {skills.map(skill => (
          <div 
            key={skill.id}
            style={{
              border: '1px solid #dcdde1',
              borderRadius: '8px',
              padding: '16px',
              backgroundColor: '#f8f9fa',
            }}
          >
            <h4 style={{ margin: '0 0 8px 0', color: '#2c3e50', fontSize: '1.2em' }}>{skill.name}</h4>
            <div style={{ fontSize: '0.9em', color: '#7f8c8d', display: 'flex', justifyContent: 'space-between' }}>
              <span>Introduced: Ch. {skill.introduced_chapter}</span>
              <span>Active Users: <strong>{skill.active_users_count}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
