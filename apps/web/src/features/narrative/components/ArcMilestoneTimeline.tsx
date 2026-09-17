import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { FormattedArcMilestone } from '../narrativeAdapters';

export interface ArcMilestoneTimelineProps {
  milestones: FormattedArcMilestone[];
  readerChapter: number;
  onInspectMilestone: (milestone: FormattedArcMilestone) => void;
}

export const ArcMilestoneTimeline: React.FC<ArcMilestoneTimelineProps> = ({
  milestones,
  readerChapter,
  onInspectMilestone,
}) => {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Arc Milestones
            </h2>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Discrete canonical state transitions ({milestones.length} total)
          </span>
        </div>
      </div>

      {milestones.length === 0 ? (
        <EmptyState
          title="No Arc Milestones Visible"
          description={`No canonical character milestones have been discovered up to Chapter ${readerChapter}.`}
        />
      ) : (
        <div
          data-testid="arc-milestones-list"
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '10px',
            maxHeight: '480px',
            overflowY: 'auto',
            paddingRight: '4px',
          }}
        >
          {milestones.map((m) => (
            <div
              key={m.id}
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
                    color: 'var(--tsi-accent-primary)',
                  }}
                >
                  {m.chapter}
                </span>
              </div>

              {/* Milestone Details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', flex: 1 }}>
                <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '6px' }}>
                  <Badge variant="default" style={{ fontSize: '0.6875rem' }}>
                    {m.milestoneType.replace(/_/g, ' ')}
                  </Badge>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                    Seq {m.sequence} • Char: {m.characterId}
                  </span>
                </div>
                <p style={{ margin: '2px 0 0', fontSize: '0.8125rem', color: 'var(--tsi-text-primary)' }}>
                  {m.description}
                </p>
              </div>

              {/* Action */}
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onInspectMilestone(m)}
                title="Inspect milestone state delta and provenance"
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
