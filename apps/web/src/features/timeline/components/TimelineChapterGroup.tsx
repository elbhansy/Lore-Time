import React from 'react';
import { EventReadModel } from '../../../api/contracts/read-models';
import { Badge } from '../../../components/ui/Badge';
import { TimelineEventItem } from './TimelineEventItem';

export interface TimelineChapterGroupProps {
  chapterNumber: number;
  isReaderHorizon: boolean;
  events: EventReadModel[];
  onSelectEvent: (event: EventReadModel) => void;
}

export const TimelineChapterGroup: React.FC<TimelineChapterGroupProps> = ({
  chapterNumber,
  isReaderHorizon,
  events,
  onSelectEvent,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        marginBottom: '16px',
        position: 'relative',
      }}
    >
      {/* Chapter Marker Header */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
          position: 'sticky',
          top: 0,
          zIndex: 10,
          backgroundColor: 'var(--tsi-canvas)',
          padding: '8px 0',
        }}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            backgroundColor: isReaderHorizon ? 'var(--tsi-temporal-scope)' : 'var(--tsi-surface-secondary)',
            border: isReaderHorizon
              ? '2px solid var(--tsi-temporal-scope-glow)'
              : '2px solid var(--tsi-border-default)',
            color: isReaderHorizon ? '#ffffff' : 'var(--tsi-text-secondary)',
            fontSize: '0.6875rem',
            fontWeight: 700,
            zIndex: 3,
            flexShrink: 0,
          }}
        >
          {chapterNumber}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span
            style={{
              fontSize: '1.125rem',
              fontWeight: 700,
              color: isReaderHorizon ? 'var(--tsi-temporal-scope)' : 'var(--tsi-text-primary)',
            }}
          >
            Chapter {chapterNumber}
          </span>

          {isReaderHorizon && (
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Current Reader Boundary
            </Badge>
          )}

          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            ({events.length} {events.length === 1 ? 'event' : 'events'})
          </span>
        </div>

        <div
          style={{
            flex: 1,
            height: '1px',
            backgroundColor: isReaderHorizon ? 'var(--tsi-temporal-scope)' : 'var(--tsi-border-subtle)',
            opacity: isReaderHorizon ? 0.6 : 1,
            marginLeft: '8px',
          }}
        />
      </div>

      {/* Events Stream within Chapter */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {events.map((evt, idx) => (
          <TimelineEventItem
            key={evt.event_id}
            event={evt}
            isLastInChapter={idx === events.length - 1}
            onSelect={onSelectEvent}
          />
        ))}
      </div>
    </div>
  );
};
