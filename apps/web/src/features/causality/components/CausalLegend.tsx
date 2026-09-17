import React from 'react';

export interface CausalLegendItem {
  label: string;
  color: string;
  style: 'solid' | 'dashed';
}

const CAUSAL_RELATIONS: CausalLegendItem[] = [
  { label: 'DIRECT_CAUSE / EVENT_CHAIN', color: '#38bdf8', style: 'solid' },
  { label: 'INDIRECT_INFLUENCE', color: '#94a3b8', style: 'dashed' },
  { label: 'STATE_TRANSITION', color: '#f59e0b', style: 'solid' },
  { label: 'CHARACTER / RELATIONSHIP', color: '#a855f7', style: 'solid' },
  { label: 'POWER_CONSEQUENCE', color: '#ef4444', style: 'solid' },
  { label: 'FACTION_CONSEQUENCE', color: '#10b981', style: 'solid' },
];

export const CausalLegend: React.FC = () => {
  return (
    <div
      data-testid="causal-legend"
      style={{
        backgroundColor: 'rgba(22, 25, 34, 0.94)',
        backdropFilter: 'blur(8px)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
        padding: '10px 14px',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.4)',
        display: 'flex',
        flexDirection: 'column',
        gap: '8px',
        pointerEvents: 'auto',
        maxWidth: '240px',
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
        Causal Relation Semantics (Phase 5.2)
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '5px' }}>
        {CAUSAL_RELATIONS.map((item) => (
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
            <span style={{ fontFamily: 'var(--tsi-font-mono)', fontSize: '0.6875rem' }}>{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
