import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { FormattedTurningPoint } from '../narrativeAdapters';

export interface TurningPointTimelineProps {
  turningPoints: FormattedTurningPoint[];
  readerChapter: number;
  onInspectTurningPoint: (tp: FormattedTurningPoint) => void;
}

export const TurningPointTimeline: React.FC<TurningPointTimelineProps> = ({
  turningPoints,
  readerChapter,
  onInspectTurningPoint,
}) => {
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
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Turning Points
            </h2>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            High-significance narrative inflection points ({turningPoints.length} total)
          </span>
        </div>
      </div>

      {turningPoints.length === 0 ? (
        <EmptyState
          title="No Turning Points Visible"
          description={`No major structural narrative turning points have occurred prior to Chapter ${readerChapter}.`}
        />
      ) : (
        <div
          data-testid="turning-points-list"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            maxHeight: '480px',
            overflowY: 'auto',
            paddingRight: '4px',
          }}
        >
          {turningPoints.map((tp) => (
            <div
              key={tp.id}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '12px',
                padding: '12px 14px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-subtle)',
                borderRadius: 'var(--tsi-radius-md)',
                transition: 'background-color 0.15s ease',
              }}
            >
              {/* Chapter & Timeline Badge */}
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  minWidth: '60px',
                  padding: '4px 6px',
                  backgroundColor: 'var(--tsi-surface-elevated)',
                  borderRadius: 'var(--tsi-radius-sm)',
                  border: '1px solid var(--tsi-border-default)',
                }}
              >
                <span style={{ fontSize: '0.625rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  CH.
                </span>
                <span
                  style={{
                    fontSize: '0.875rem',
                    fontWeight: 700,
                    fontFamily: 'var(--tsi-font-mono)',
                    color: 'var(--tsi-status-warning)',
                  }}
                >
                  {tp.chapter}
                </span>
              </div>

              {/* Turning Point Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px' }}>
                  <Badge variant={getSignificanceVariant(tp.significance)} style={{ fontSize: '0.6875rem' }}>
                    {tp.significance.toUpperCase()}
                  </Badge>
                  <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--tsi-text-primary)' }}>
                    {tp.turningPointType.replace(/_/g, ' ')}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                    • Char: {tp.characterId}
                  </span>
                </div>

                <p style={{ margin: '2px 0 0', fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
                  {tp.description}
                </p>

                {tp.affectedDimensions.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                    {tp.affectedDimensions.map((dim) => (
                      <Badge key={dim} variant="neutral" style={{ fontSize: '0.625rem' }}>
                        {dim}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              {/* Action */}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onInspectTurningPoint(tp)}
                title="Inspect turning point resulting state and evidence"
              >
                Inspect ↗
              </Button>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
