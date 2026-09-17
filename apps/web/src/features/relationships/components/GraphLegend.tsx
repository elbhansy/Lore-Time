import React from 'react';

export interface LegendItem {
  label: string;
  color: string;
  style: 'solid' | 'dashed';
}

const RELATIONSHIP_TYPES: LegendItem[] = [
  { label: 'Allied / Friend', color: '#10b981', style: 'solid' },
  { label: 'Enemy / Rival', color: '#ef4444', style: 'dashed' },
  { label: 'Family / Kin', color: '#8b5cf6', style: 'solid' },
  { label: 'Master / Mentor', color: '#f59e0b', style: 'solid' },
  { label: 'Commander / Subordinate', color: '#38bdf8', style: 'solid' },
  { label: 'Affiliated / General', color: '#64748b', style: 'solid' },
];

export const GraphLegend: React.FC = () => {
  return (
    <div
      data-testid="graph-legend"
      style={{
        backgroundColor: 'rgba(22, 25, 34, 0.92)',
        backdropFilter: 'blur(8px)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
        padding: '10px 14px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        pointerEvents: 'auto',
        maxWidth: '220px',
      }}
    >
      <div
        style={{
          fontSize: '0.6875rem',
          fontWeight: 700,
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
          color: 'var(--tsi-text-muted)',
        }}
      >
        Relationship Topology Legend
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {RELATIONSHIP_TYPES.map((item) => (
          <div
            key={item.label}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '0.75rem',
              color: 'var(--tsi-text-secondary)',
            }}
          >
            <span
              style={{
                display: 'inline-block',
                width: '18px',
                height: 0,
                borderTop: `2px ${item.style} ${item.color}`,
              }}
            />
            <span>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
