import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';

export interface CanonicalContextBarProps {
  seriesId: string;
  readerChapter: number;
  totalCharactersVisible: number;
  totalEventsVisible: number;
}

export const CanonicalContextBar: React.FC<CanonicalContextBarProps> = ({
  seriesId: _seriesId,
  readerChapter,
  totalCharactersVisible,
  totalEventsVisible,
}) => {
  return (
    <Card
      data-testid="canonical-context-bar"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        padding: '12px 18px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Badge variant="success" style={{ fontSize: '0.6875rem' }}>
          CANONICAL BASELINE
        </Badge>
        <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          Simulation Anchor: <strong>Chapter {readerChapter}</strong>
        </span>
        <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)' }}>
          ({totalCharactersVisible} characters • {totalEventsVisible} events)
        </span>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
          Safety Guarantee:
        </span>
        <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
          Zero Canonical DB Mutation
        </Badge>
        <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
          Ephemeral Memory Sandbox
        </Badge>
      </div>
    </Card>
  );
};
