import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { EventReadModel } from '../../../api/contracts/read-models';
import { useShellContext } from '../../../state/shell/shell-context';

export interface TimelinePreviewProps {
  seriesId: string;
  readerChapter: number;
  events: EventReadModel[];
}

export const TimelinePreview: React.FC<TimelinePreviewProps> = ({
  seriesId,
  readerChapter,
  events,
}) => {
  const navigate = useNavigate();
  const { openInspector } = useShellContext();

  const handleEventClick = (evt: EventReadModel) => {
    openInspector({
      title: evt.title,
      subtitle: `Chapter ${evt.chapter_number} • Seq ${evt.sequence}`,
      badge: {
        label: evt.event_type,
        variant: evt.is_turning_point ? 'warning' : 'neutral',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Description
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{evt.description}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Subject
              </span>
              <p style={{ margin: '2px 0 0', color: 'var(--tsi-text-secondary)', fontFamily: 'var(--tsi-font-mono)', fontSize: '0.8125rem' }}>
                {evt.subject_type}: {evt.subject_id}
              </p>
            </div>
            {evt.target_id && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Target
                </span>
                <p style={{ margin: '2px 0 0', color: 'var(--tsi-text-secondary)', fontFamily: 'var(--tsi-font-mono)', fontSize: '0.8125rem' }}>
                  {evt.target_type}: {evt.target_id}
                </p>
              </div>
            )}
          </div>

          {Object.keys(evt.previous_state).length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Previous State
              </span>
              <pre
                style={{
                  margin: '4px 0 0',
                  padding: '8px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  borderRadius: 'var(--tsi-radius-sm)',
                  fontSize: '0.75rem',
                  overflowX: 'auto',
                }}
              >
                {JSON.stringify(evt.previous_state, null, 2)}
              </pre>
            </div>
          )}

          {Object.keys(evt.new_state).length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Resulting State
              </span>
              <pre
                style={{
                  margin: '4px 0 0',
                  padding: '8px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  borderRadius: 'var(--tsi-radius-sm)',
                  fontSize: '0.75rem',
                  overflowX: 'auto',
                }}
              >
                {JSON.stringify(evt.new_state, null, 2)}
              </pre>
            </div>
          )}

          <Button
            size="sm"
            variant="secondary"
            onClick={() => navigate(`/series/${seriesId}/timeline`)}
          >
            Investigate in Full Timeline ↗
          </Button>
        </div>
      ),
    });
  };

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Recent Canonical Events
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Latest chronological occurrences known up to Chapter {readerChapter}
          </span>
        </div>

        <Button
          size="sm"
          variant="ghost"
          onClick={() => navigate(`/series/${seriesId}/timeline`)}
          title="Explore complete chronological feed"
        >
          View Full Timeline ({events.length}) →
        </Button>
      </div>

      {events.length === 0 ? (
        <EmptyState
          title="No Events Recorded"
          description={`No story events have transpired up to Chapter ${readerChapter}. Advance the temporal horizon to observe story progress.`}
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {events.map((evt) => (
            <div
              key={evt.event_id}
              onClick={() => handleEventClick(evt)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') handleEventClick(evt); }}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '10px 14px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                borderRadius: 'var(--tsi-radius-md)',
                border: '1px solid var(--tsi-border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', minWidth: 0 }}>
                <Badge variant="neutral" style={{ fontFamily: 'var(--tsi-font-mono)', fontSize: '0.6875rem', flexShrink: 0 }}>
                  Ch. {evt.chapter_number}
                </Badge>

                <div style={{ display: 'flex', flexDirection: 'column', minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span
                      style={{
                        fontWeight: 600,
                        fontSize: '0.875rem',
                        color: 'var(--tsi-text-primary)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {evt.title}
                    </span>
                    {evt.is_milestone && <Badge variant="default" style={{ fontSize: '0.625rem' }}>Milestone</Badge>}
                    {evt.is_turning_point && <Badge variant="warning" style={{ fontSize: '0.625rem' }}>Turning Point</Badge>}
                  </div>
                  <span
                    style={{
                      fontSize: '0.75rem',
                      color: 'var(--tsi-text-secondary)',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                    }}
                  >
                    {evt.description}
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', flexShrink: 0, marginLeft: '12px' }}>
                <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
                  Seq {evt.sequence}
                </Badge>
                <span style={{ color: 'var(--tsi-text-muted)', fontSize: '0.875rem' }}>›</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
