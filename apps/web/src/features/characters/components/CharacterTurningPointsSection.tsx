import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { TurningPointDTO } from '../../../api/contracts/read-models';

export interface CharacterTurningPointsSectionProps {
  turningPoints: TurningPointDTO[];
  readerChapter: number;
  onInspectTurningPoint: (tp: TurningPointDTO) => void;
}

export const CharacterTurningPointsSection: React.FC<CharacterTurningPointsSectionProps> = ({
  turningPoints,
  readerChapter,
  onInspectTurningPoint,
}) => {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Authoritative Turning Points ({turningPoints.length})
          </h2>
          <Badge variant="warning" style={{ fontSize: '0.6875rem' }}>
            Known Through Ch. {readerChapter}
          </Badge>
        </div>
        <p style={{ margin: '4px 0 0', fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          High-impact structural events causing non-linear shifts in status, alliance, or character trajectory.
        </p>
      </div>

      {turningPoints.length === 0 ? (
        <EmptyState
          title="No Turning Points Recorded"
          description="No pivotal turning points have altered this character's destiny by the current knowledge horizon."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {turningPoints.map((tp) => {
            const isCritical = tp.significance === 'critical' || tp.significance === 'high';
            return (
              <div
                key={tp.turning_point_id}
                onClick={() => onInspectTurningPoint(tp)}
                role="button"
                tabIndex={0}
                aria-label={`Turning point: ${tp.description}, Chapter ${tp.chapter}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onInspectTurningPoint(tp);
                  }
                }}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  padding: '12px 16px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  border: isCritical
                    ? '1px solid var(--tsi-border-emphasis)'
                    : '1px solid var(--tsi-border-subtle)',
                  borderRadius: 'var(--tsi-radius-md)',
                  cursor: 'pointer',
                  transition: 'background-color 0.12s ease',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
                      Ch. {tp.chapter}
                    </Badge>
                    <Badge
                      variant={isCritical ? 'warning' : 'neutral'}
                      style={{ fontSize: '0.625rem', textTransform: 'uppercase' }}
                    >
                      {tp.significance}
                    </Badge>
                    <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>
                      {tp.turning_point_type}
                    </Badge>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tsi-accent-primary)' }}>
                    Inspect Impact 🔍
                  </span>
                </div>

                <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--tsi-text-primary)', lineHeight: 1.4 }}>
                  {tp.description}
                </p>

                {/* Affected Dimensions Chips */}
                {tp.affected_dimensions && tp.affected_dimensions.length > 0 && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexWrap: 'wrap' }}>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                      Impact:
                    </span>
                    {tp.affected_dimensions.map((dim) => (
                      <Badge key={dim} variant="neutral" style={{ fontSize: '0.625rem' }}>
                        {dim}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
