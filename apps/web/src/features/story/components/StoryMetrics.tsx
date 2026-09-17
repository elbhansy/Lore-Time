import React from 'react';
import { Card } from '../../../components/ui/Card';

export interface StoryMetricsProps {
  totalChaptersVisible: number;
  totalEventsVisible: number;
  totalCharactersVisible: number;
  totalFactionsVisible: number;
  totalRelationshipsActive: number;
}

export const StoryMetrics: React.FC<StoryMetricsProps> = ({
  totalChaptersVisible,
  totalEventsVisible,
  totalCharactersVisible,
  totalFactionsVisible,
  totalRelationshipsActive,
}) => {
  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))',
        gap: '12px',
      }}
    >
      <Card style={{ padding: '14px 16px' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Visible Chapters
        </span>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--tsi-text-primary)', marginTop: '2px' }}>
          {totalChaptersVisible}
        </div>
      </Card>

      <Card style={{ padding: '14px 16px' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Known Events
        </span>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--tsi-text-primary)', marginTop: '2px' }}>
          {totalEventsVisible}
        </div>
      </Card>

      <Card style={{ padding: '14px 16px' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Introduced Characters
        </span>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--tsi-text-primary)', marginTop: '2px' }}>
          {totalCharactersVisible}
        </div>
      </Card>

      <Card style={{ padding: '14px 16px' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Active Factions
        </span>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--tsi-text-primary)', marginTop: '2px' }}>
          {totalFactionsVisible}
        </div>
      </Card>

      <Card style={{ padding: '14px 16px' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Active Relationships
        </span>
        <div style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--tsi-text-primary)', marginTop: '2px' }}>
          {totalRelationshipsActive}
        </div>
      </Card>
    </div>
  );
};
