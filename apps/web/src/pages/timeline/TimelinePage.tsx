import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTimelineFeed } from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { TimelineHeader } from '../../features/timeline/components/TimelineHeader';
import { TimelineChapterGroup } from '../../features/timeline/components/TimelineChapterGroup';
import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { Button } from '../../components/ui/Button';
import { EventReadModel } from '../../api/contracts/read-models';

export const TimelinePage: React.FC = () => {
  const { seriesId: routeSeriesId } = useParams<{ seriesId: string }>();
  const {
    seriesId: contextSeriesId,
    readerChapter,
    totalChapters = 200,
    stepForward,
    stepBackward,
    setReaderChapter,
    canStepForward,
    canStepBackward,
  } = useTemporalContext();

  const activeSeriesId = routeSeriesId || contextSeriesId;
  const { openInspector } = useShellContext();
  const navigate = useNavigate();

  // Query timeline feed bounded by readerChapter
  const { data, isLoading, isError, error, refetch } = useTimelineFeed(
    activeSeriesId,
    readerChapter,
    { from: 1, to: readerChapter, limit: 100, offset: 0 }
  );

  // Group events by chapter number
  const chapterGroups = useMemo(() => {
    if (!data?.events) return [];
    
    // Defensive check: filter out any events beyond readerChapter (Temporal Firewall)
    const validEvents = data.events.filter((e) => e.chapter_number <= readerChapter);

    const map = new Map<number, EventReadModel[]>();
    for (const evt of validEvents) {
      const ch = evt.chapter_number;
      if (!map.has(ch)) {
        map.set(ch, []);
      }
      map.get(ch)!.push(evt);
    }

    const sortedChapters = Array.from(map.keys()).sort((a, b) => a - b);
    return sortedChapters.map((ch) => ({
      chapterNumber: ch,
      isReaderHorizon: ch === readerChapter,
      events: map.get(ch)!.sort((a, b) => a.sequence - b.sequence),
    }));
  }, [data?.events, readerChapter]);

  // Context Inspector integration for an individual event
  const handleSelectEvent = (evt: EventReadModel) => {
    openInspector({
      title: evt.title,
      subtitle: `Chapter ${evt.chapter_number} • Sequence ${evt.sequence}`,
      badge: {
        label: evt.event_type,
        variant: evt.is_turning_point ? 'warning' : 'neutral',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Canonical Description
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{evt.description}</p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Subject
              </span>
              <p style={{ margin: '2px 0 0', color: 'var(--tsi-text-secondary)', fontFamily: 'var(--tsi-font-mono)', fontSize: '0.8125rem' }}>
                {evt.subject_type}:{evt.subject_id}
              </p>
            </div>
            {evt.target_id && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Target
                </span>
                <p style={{ margin: '2px 0 0', color: 'var(--tsi-text-secondary)', fontFamily: 'var(--tsi-font-mono)', fontSize: '0.8125rem' }}>
                  {evt.target_type}:{evt.target_id}
                </p>
              </div>
            )}
          </div>

          {/* Causes List */}
          {evt.causes.length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Direct Causes ({evt.causes.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                {evt.causes.map((c) => (
                  <div
                    key={c.relation_id}
                    style={{
                      padding: '6px 8px',
                      backgroundColor: 'var(--tsi-surface-secondary)',
                      borderRadius: 'var(--tsi-radius-sm)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{c.relation_type}</span> from Ch. {c.source_chapter} (Score: {c.impact_score})
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Effects List */}
          {evt.effects.length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Propagated Effects ({evt.effects.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '4px' }}>
                {evt.effects.map((e) => (
                  <div
                    key={e.relation_id}
                    style={{
                      padding: '6px 8px',
                      backgroundColor: 'var(--tsi-surface-secondary)',
                      borderRadius: 'var(--tsi-radius-sm)',
                      fontSize: '0.8125rem',
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>{e.relation_type}</span> to Ch. {e.target_chapter} (Score: {e.impact_score})
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* State Transition Delta */}
          {Object.keys(evt.new_state).length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                State Transition
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

          {/* Deep Exploration Actions */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
            <Button
              size="sm"
              variant="primary"
              onClick={() => navigate(`/series/${activeSeriesId}/causality`)}
            >
              Trace Causal Path ↗
            </Button>
            {evt.subject_type === 'CHAR' && (
              <Button
                size="sm"
                variant="secondary"
                onClick={() => navigate(`/series/${activeSeriesId}/characters/${encodeURIComponent(evt.subject_id)}`)}
              >
                Subject Arc ↗
              </Button>
            )}
          </div>
        </div>
      ),
    });
  };

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        padding: '24px 32px',
        maxWidth: '1280px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* Milestone 3: Temporal Header */}
      <TimelineHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        totalVisibleEvents={data?.total_events || 0}
        fromChapter={data?.from_chapter || 1}
        toChapter={data?.to_chapter || readerChapter}
        onJumpToStart={() => setReaderChapter(1)}
        onStepBackward={stepBackward}
        onStepForward={stepForward}
        onJumpToHorizon={() => setReaderChapter(totalChapters)}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Loading Skeleton */}
      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Skeleton height={60} />
          <Skeleton height={100} />
          <Skeleton height={100} />
          <Skeleton height={60} />
          <Skeleton height={100} />
        </div>
      )}

      {/* Error State */}
      {isError && (
        <ErrorState
          title="Failed to Load Timeline Stream"
          message={error?.message || 'Unable to retrieve chronological feed from Intelligence Core.'}
          status={error?.status}
          onRetry={() => refetch()}
        />
      )}

      {/* Populated Timeline Stream */}
      {!isLoading && !isError && chapterGroups.length === 0 && (
        <EmptyState
          title="No Events in Horizon"
          description={`No story events exist between Chapter 1 and Chapter ${readerChapter}. Advance your reader horizon to explore newly transpired events.`}
          actionLabel="Advance to Next Chapter"
          onAction={stepForward}
        />
      )}

      {!isLoading && !isError && chapterGroups.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {chapterGroups.map((group) => (
            <TimelineChapterGroup
              key={group.chapterNumber}
              chapterNumber={group.chapterNumber}
              isReaderHorizon={group.isReaderHorizon}
              events={group.events}
              onSelectEvent={handleSelectEvent}
            />
          ))}

          {/* End of Current Knowledge Horizon Banner */}
          <div
            style={{
              padding: '16px 20px',
              backgroundColor: 'var(--tsi-surface-primary)',
              border: '1px dashed var(--tsi-temporal-scope)',
              borderRadius: 'var(--tsi-radius-md)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginTop: '16px',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ fontSize: '1.25rem', color: 'var(--tsi-temporal-scope)' }}>⏳</span>
              <div>
                <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                  Current Knowledge Horizon Reached (Chapter {readerChapter})
                </span>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                  Future story events beyond Chapter {readerChapter} are withheld to prevent spoilers.
                </p>
              </div>
            </div>

            {readerChapter < totalChapters && (
              <Button size="sm" variant="primary" onClick={stepForward}>
                Advance to Chapter {readerChapter + 1} →
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
