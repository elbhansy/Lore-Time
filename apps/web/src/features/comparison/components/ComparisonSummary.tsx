import React from 'react';

interface ComparisonSummaryProps {
  summary: {
    characters_introduced: number;
    characters_removed: number;
    power_changes: number;
    skills_unlocked: number;
    relationships_changed: number;
  };
}

export const ComparisonSummary: React.FC<ComparisonSummaryProps> = ({ summary }) => {
  const statBoxStyle = {
    flex: 1,
    padding: '16px',
    backgroundColor: 'white',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    textAlign: 'center' as const,
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
  };

  const numberStyle = {
    fontSize: '1.5em',
    fontWeight: 'bold',
    marginBottom: '8px',
  };

  return (
    <div style={{ display: 'flex', gap: '16px', marginBottom: '32px' }}>
      <div style={{ ...statBoxStyle, borderTop: '4px solid #3498db' }}>
        <div style={{ ...numberStyle, color: '#3498db' }}>
          +{summary.characters_introduced} <span style={{fontSize: '0.6em', color: '#7f8c8d'}}>/ -{summary.characters_removed}</span>
        </div>
        <div style={{ fontSize: '0.9em', color: '#555' }}>Characters</div>
      </div>
      
      <div style={{ ...statBoxStyle, borderTop: '4px solid #e67e22' }}>
        <div style={{ ...numberStyle, color: '#e67e22' }}>{summary.power_changes}</div>
        <div style={{ fontSize: '0.9em', color: '#555' }}>Power Changes</div>
      </div>
      
      <div style={{ ...statBoxStyle, borderTop: '4px solid #9b59b6' }}>
        <div style={{ ...numberStyle, color: '#9b59b6' }}>+{summary.skills_unlocked}</div>
        <div style={{ fontSize: '0.9em', color: '#555' }}>Skills Unlocked</div>
      </div>
      
      <div style={{ ...statBoxStyle, borderTop: '4px solid #2ecc71' }}>
        <div style={{ ...numberStyle, color: '#2ecc71' }}>{summary.relationships_changed}</div>
        <div style={{ fontSize: '0.9em', color: '#555' }}>Relationship Changes</div>
      </div>
    </div>
  );
};
