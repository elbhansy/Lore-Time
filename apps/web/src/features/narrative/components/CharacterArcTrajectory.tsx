import React from 'react';
import { Badge } from '../../../components/ui/Badge';
import { ArcTrajectorySummaryDTO } from '../../../api/contracts/read-models';

export interface CharacterArcTrajectoryProps {
  trajectory: ArcTrajectorySummaryDTO | null;
  readerChapter: number;
}

export const CharacterArcTrajectory: React.FC<CharacterArcTrajectoryProps> = ({
  trajectory,
  readerChapter,
}) => {
  if (!trajectory) {
    return (
      <div
        style={{
          padding: '12px 14px',
          backgroundColor: 'var(--tsi-surface-secondary)',
          borderRadius: 'var(--tsi-radius-md)',
          border: '1px solid var(--tsi-border-subtle)',
          fontSize: '0.8125rem',
          color: 'var(--tsi-text-muted)',
        }}
      >
        No quantitative arc trajectory summary available for this character at Chapter {readerChapter}.
      </div>
    );
  }

  const getStatusVariant = (status: string) => {
    switch (status.toLowerCase()) {
      case 'alive':
        return 'success';
      case 'dead':
        return 'error';
      default:
        return 'neutral';
    }
  };

  const getSignificanceVariant = (sig: string) => {
    switch (sig.toUpperCase()) {
      case 'CRITICAL':
        return 'error';
      case 'HIGH':
        return 'warning';
      case 'MEDIUM':
        return 'temporal';
      default:
        return 'neutral';
    }
  };

  return (
    <div
      data-testid="character-arc-trajectory"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '12px',
        padding: '14px 16px',
        backgroundColor: 'var(--tsi-surface-secondary)',
        borderRadius: 'var(--tsi-radius-md)',
        border: '1px solid var(--tsi-border-subtle)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Canonical Arc Trajectory
        </span>
        <div style={{ display: 'flex', gap: '6px' }}>
          <Badge variant={getStatusVariant(trajectory.current_status)} style={{ fontSize: '0.6875rem' }}>
            {trajectory.current_status.toUpperCase()}
          </Badge>
          <Badge variant={getSignificanceVariant(trajectory.highest_significance)} style={{ fontSize: '0.6875rem' }}>
            MAX SIG: {trajectory.highest_significance.toUpperCase()}
          </Badge>
        </div>
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(110px, 1fr))',
          gap: '8px',
        }}
      >
        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'var(--tsi-surface-elevated)',
            borderRadius: 'var(--tsi-radius-sm)',
            border: '1px solid var(--tsi-border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.625rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Rank
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {trajectory.current_rank || 'Unranked'}
          </div>
        </div>

        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'var(--tsi-surface-elevated)',
            borderRadius: 'var(--tsi-radius-sm)',
            border: '1px solid var(--tsi-border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.625rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Faction
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {trajectory.current_faction || 'None'}
          </div>
        </div>

        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'var(--tsi-surface-elevated)',
            borderRadius: 'var(--tsi-radius-sm)',
            border: '1px solid var(--tsi-border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.625rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Skills Unlocked
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--tsi-accent-primary)' }}>
            {trajectory.total_skills_unlocked}
          </div>
        </div>

        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'var(--tsi-surface-elevated)',
            borderRadius: 'var(--tsi-radius-sm)',
            border: '1px solid var(--tsi-border-subtle)',
          }}
        >
          <div style={{ fontSize: '0.625rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Relationships
          </div>
          <div style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {trajectory.total_relationships}
          </div>
        </div>
      </div>
    </div>
  );
};
