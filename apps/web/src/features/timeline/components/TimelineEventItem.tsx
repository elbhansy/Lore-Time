import React from 'react';
import { EventReadModel } from '../../../api/contracts/read-models';
import { Badge } from '../../../components/ui/Badge';

export interface TimelineEventItemProps {
  event: EventReadModel;
  isLastInChapter?: boolean;
  onSelect: (event: EventReadModel) => void;
}

export const TimelineEventItem: React.FC<TimelineEventItemProps> = ({
  event,
  isLastInChapter = false,
  onSelect,
}) => {
  const isTurningPoint = event.is_turning_point;
  const isMilestone = event.is_milestone;

  return (
    <div
      onClick={() => onSelect(event)}
      role="button"
      tabIndex={0}
      aria-label={`Event: ${event.title}, Chapter ${event.chapter_number}`}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          onSelect(event);
        }
      }}
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        position: 'relative',
        paddingLeft: '32px',
        paddingBottom: isLastInChapter ? '16px' : '20px',
        cursor: 'pointer',
      }}
    >
      {/* Vertical Spine Line */}
      <div
        style={{
          position: 'absolute',
          left: '11px',
          top: '16px',
          bottom: 0,
          width: '2px',
          backgroundColor: 'var(--tsi-border-subtle)',
          display: isLastInChapter ? 'none' : 'block',
        }}
      />

      {/* Node Bullet Marker on the Spine */}
      <div
        style={{
          position: 'absolute',
          left: '5px',
          top: '4px',
          width: isTurningPoint ? '14px' : '12px',
          height: isTurningPoint ? '14px' : '12px',
          borderRadius: '50%',
          backgroundColor: isTurningPoint
            ? 'var(--tsi-status-warning)'
            : isMilestone
            ? 'var(--tsi-accent-primary)'
            : 'var(--tsi-surface-elevated)',
          border: isTurningPoint
            ? '3px solid var(--tsi-canvas)'
            : '2px solid var(--tsi-border-strong)',
          boxShadow: isTurningPoint ? '0 0 8px rgba(245, 158, 11, 0.4)' : 'none',
          transition: 'all 0.15s ease',
          zIndex: 2,
        }}
      />

      {/* Event Details Card */}
      <div
        style={{
          flex: 1,
          backgroundColor: 'var(--tsi-surface-primary)',
          border: isTurningPoint
            ? '1px solid rgba(245, 158, 11, 0.4)'
            : '1px solid var(--tsi-border-subtle)',
          borderLeft: isTurningPoint
            ? '3px solid var(--tsi-status-warning)'
            : isMilestone
            ? '3px solid var(--tsi-accent-primary)'
            : '1px solid var(--tsi-border-subtle)',
          borderRadius: 'var(--tsi-radius-md)',
          padding: '12px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          transition: 'all 0.15s ease',
        }}
      >
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span
              style={{
                fontWeight: 600,
                fontSize: '0.9375rem',
                color: 'var(--tsi-text-primary)',
              }}
            >
              {event.title}
            </span>

            {isTurningPoint && (
              <Badge variant="warning" style={{ fontSize: '0.625rem', textTransform: 'uppercase' }}>
                Turning Point
              </Badge>
            )}

            {isMilestone && (
              <Badge variant="default" style={{ fontSize: '0.625rem', textTransform: 'uppercase' }}>
                Milestone
              </Badge>
            )}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
              Seq {event.sequence}
            </Badge>
            <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
              {event.event_type}
            </span>
          </div>
        </div>

        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)', lineHeight: 1.4 }}>
          {event.description}
        </p>

        {/* Causal & Target Affordance Badges */}
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            alignItems: 'center',
            gap: '8px',
            marginTop: '4px',
            fontSize: '0.75rem',
            color: 'var(--tsi-text-muted)',
          }}
        >
          <span style={{ fontFamily: 'var(--tsi-font-mono)' }}>
            Subject: {event.subject_type}:{event.subject_id}
          </span>

          {event.target_id && (
            <>
              <span>•</span>
              <span style={{ fontFamily: 'var(--tsi-font-mono)' }}>
                Target: {event.target_type}:{event.target_id}
              </span>
            </>
          )}

          {event.causes.length > 0 && (
            <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>
              Causes: {event.causes.length}
            </Badge>
          )}

          {event.effects.length > 0 && (
            <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>
              Effects: {event.effects.length}
            </Badge>
          )}

          <span style={{ marginLeft: 'auto', color: 'var(--tsi-accent-primary)', fontSize: '0.75rem', fontWeight: 500 }}>
            Inspect Details ›
          </span>
        </div>
      </div>
    </div>
  );
};
