import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { TurningPointDTO } from '../../../api/contracts/read-models';
import { useShellContext } from '../../../state/shell/shell-context';

export interface TurningPointsListProps {
  seriesId: string;
  readerChapter: number;
  turningPoints: TurningPointDTO[];
}

export const TurningPointsList: React.FC<TurningPointsListProps> = ({
  seriesId,
  readerChapter,
  turningPoints,
}) => {
  const navigate = useNavigate();
  const { openInspector } = useShellContext();

  const handleTurningPointClick = (tp: TurningPointDTO) => {
    openInspector({
      title: `${tp.turning_point_type} Turning Point`,
      subtitle: `Character: ${tp.character_id} • Chapter ${tp.chapter}`,
      badge: {
        label: tp.significance.toUpperCase(),
        variant: tp.significance === 'high' || tp.significance === 'critical' ? 'warning' : 'temporal',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Turning Point Description
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{tp.description}</p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Affected Dimensions
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
              {tp.affected_dimensions.map((dim) => (
                <Badge key={dim} variant="neutral" style={{ fontSize: '0.6875rem' }}>
                  {dim}
                </Badge>
              ))}
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <Button
              size="sm"
              variant="primary"
              onClick={() => navigate(`/series/${seriesId}/characters/${encodeURIComponent(tp.character_id)}`)}
            >
              Inspect Character Arc ↗
            </Button>
            <Button
              size="sm"
              variant="secondary"
              onClick={() => navigate(`/series/${seriesId}/causality`)}
            >
              Trace Causal Path ↗
            </Button>
          </div>
        </div>
      ),
    });
  };

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Key Turning Points
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            High-significance narrative inflection points within Chapter {readerChapter}
          </span>
        </div>

        <Button
          size="sm"
          variant="ghost"
          onClick={() => navigate(`/series/${seriesId}/causality`)}
          title="Explore causal turning point chains"
        >
          Explore Causality →
        </Button>
      </div>

      {turningPoints.length === 0 ? (
        <EmptyState
          title="No Turning Points Recorded"
          description={`No character arc turning points have occurred up to Chapter ${readerChapter}.`}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {turningPoints.map((tp) => (
            <div
              key={tp.turning_point_id}
              onClick={() => handleTurningPointClick(tp)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleTurningPointClick(tp); }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                padding: '12px 14px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                borderRadius: 'var(--tsi-radius-md)',
                borderLeft: '4px solid var(--tsi-accent-primary)',
                borderTop: '1px solid var(--tsi-border-subtle)',
                borderRight: '1px solid var(--tsi-border-subtle)',
                borderBottom: '1px solid var(--tsi-border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                    {tp.turning_point_type}
                  </span>
                  <Badge
                    variant={tp.significance === 'critical' ? 'warning' : 'neutral'}
                    style={{ fontSize: '0.625rem', textTransform: 'uppercase' }}
                  >
                    {tp.significance}
                  </Badge>
                </div>

                <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
                  Ch. {tp.chapter}
                </Badge>
              </div>

              <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)', lineHeight: 1.4 }}>
                {tp.description}
              </p>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '2px' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', fontFamily: 'var(--tsi-font-mono)' }}>
                  Character: {tp.character_id}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--tsi-accent-primary)', fontWeight: 500 }}>
                  Inspect Details ›
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
