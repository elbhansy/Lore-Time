import React from 'react';
import { Handle, Position } from '@xyflow/react';

export interface GraphCharacterNodeData {
  id: string;
  label: string;
  nodeType: string;
  chapter?: number | null;
  metadata?: Record<string, unknown>;
  isSelected?: boolean;
}

export const GraphCharacterNode: React.FC<{ data: GraphCharacterNodeData }> = ({ data }) => {
  const isSelected = !!data.isSelected;

  return (
    <div
      tabIndex={0}
      role="button"
      aria-label={`Character Node: ${data.label}`}
      style={{
        padding: '10px 14px',
        minWidth: '130px',
        backgroundColor: isSelected ? 'var(--tsi-surface-elevated)' : 'var(--tsi-surface-secondary)',
        border: isSelected ? '2px solid var(--tsi-accent-primary)' : '1px solid var(--tsi-border-default)',
        borderRadius: 'var(--tsi-radius-md)',
        boxShadow: isSelected
          ? '0 0 16px rgba(99, 102, 241, 0.4), 0 4px 12px rgba(0, 0, 0, 0.5)'
          : '0 2px 8px rgba(0, 0, 0, 0.3)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: '4px',
        cursor: 'pointer',
        transition: 'all 0.15s ease',
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{
          background: isSelected ? 'var(--tsi-accent-primary)' : 'var(--tsi-border-default)',
          width: 7,
          height: 7,
          border: 'none',
        }}
      />

      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isSelected ? 'var(--tsi-accent-primary)' : 'var(--tsi-status-success)',
          }}
        />
        <span
          style={{
            fontWeight: 600,
            fontSize: '0.875rem',
            color: 'var(--tsi-text-primary)',
            textAlign: 'center',
            letterSpacing: '-0.01em',
          }}
        >
          {data.label}
        </span>
      </div>

      <div
        style={{
          fontSize: '0.6875rem',
          color: 'var(--tsi-text-muted)',
          fontFamily: 'var(--tsi-font-mono)',
        }}
      >
        ID: {data.id}
      </div>

      {isSelected && (
        <span
          style={{
            fontSize: '0.625rem',
            fontWeight: 600,
            color: 'var(--tsi-accent-primary)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
            marginTop: '2px',
          }}
        >
          ● Selected
        </span>
      )}

      <Handle
        type="source"
        position={Position.Bottom}
        style={{
          background: isSelected ? 'var(--tsi-accent-primary)' : 'var(--tsi-border-default)',
          width: 7,
          height: 7,
          border: 'none',
        }}
      />
    </div>
  );
};
