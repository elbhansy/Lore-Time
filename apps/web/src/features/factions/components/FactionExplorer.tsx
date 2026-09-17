import React from 'react';
import { useReader } from '../../reader/reader-store';
import { useFactions } from '../hooks/useFactions';
import { useNavigate } from 'react-router-dom';

export const FactionExplorer: React.FC = () => {
  const { seriesId, readerChapter } = useReader();
  const navigate = useNavigate();
  const { data: factions, isLoading, isError } = useFactions(seriesId, readerChapter);

  if (isLoading) return <p>Loading factions...</p>;
  if (isError) return <p style={{ color: 'red' }}>Failed to load factions.</p>;
  if (!factions || factions.length === 0) return <p style={{ color: '#7f8c8d' }}>No factions introduced up to Chapter {readerChapter}.</p>;

  return (
    <div style={{ marginTop: '24px' }}>
      <h3>Factions & Organizations</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '16px', marginTop: '16px' }}>
        {factions.map(faction => (
          <div 
            key={faction.id} 
            onClick={() => navigate(`/series/${seriesId}/factions/${faction.id}?chapter=${readerChapter}`)}
            style={{
              border: '1px solid #dcdde1',
              borderRadius: '8px',
              padding: '16px',
              cursor: 'pointer',
              backgroundColor: '#f8f9fa',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
            }}
            onMouseOver={e => e.currentTarget.style.transform = 'translateY(-2px)'}
            onMouseOut={e => e.currentTarget.style.transform = 'translateY(0)'}
          >
            <h4 style={{ margin: '0 0 8px 0', color: '#2c3e50', fontSize: '1.2em' }}>{faction.name}</h4>
            <div style={{ fontSize: '0.9em', color: '#7f8c8d', display: 'flex', justifyContent: 'space-between' }}>
              <span>Introduced: Ch. {faction.introduced_chapter}</span>
              <span>Active Members: <strong>{faction.member_count}</strong></span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
