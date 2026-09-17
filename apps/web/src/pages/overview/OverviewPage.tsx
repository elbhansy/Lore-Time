import React from 'react';
import { useParams } from 'react-router-dom';
import { useStoryOverview } from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { StoryIdentityHeader } from '../../features/story/components/StoryIdentityHeader';
import { StoryMetrics } from '../../features/story/components/StoryMetrics';
import { TimelinePreview } from '../../features/story/components/TimelinePreview';
import { TurningPointsList } from '../../features/story/components/TurningPointsList';
import { CharacterRoster } from '../../features/story/components/CharacterRoster';

export const OverviewPage: React.FC = () => {
  const { seriesId: routeSeriesId } = useParams<{ seriesId: string }>();
  const { seriesId: contextSeriesId, readerChapter, totalChapters = 200 } = useTemporalContext();
  const activeSeriesId = routeSeriesId || contextSeriesId;

  const { data, isLoading, isError, error, refetch } = useStoryOverview(
    activeSeriesId,
    readerChapter
  );

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '24px',
        padding: '24px 32px',
        maxWidth: '1440px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* Loading Skeleton State */}
      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <Skeleton height={180} borderRadius="var(--tsi-radius-lg)" />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: '12px' }}>
            <Skeleton height={80} />
            <Skeleton height={80} />
            <Skeleton height={80} />
            <Skeleton height={80} />
            <Skeleton height={80} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '20px' }}>
            <Skeleton height={320} />
            <Skeleton height={320} />
          </div>
          <Skeleton height={160} />
        </div>
      )}

      {/* Error State with Status and Retry Action */}
      {isError && (
        <ErrorState
          title="Failed to Load Story Overview"
          message={error?.message || 'Unable to retrieve read model from Intelligence Core.'}
          status={error?.status}
          onRetry={() => refetch()}
        />
      )}

      {/* Populated Production Overview Experience */}
      {data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Milestone 2 & 3: Story Identity and Temporal Position */}
          <StoryIdentityHeader
            seriesId={data.series_id}
            seriesTitle={data.series_title}
            readerChapter={readerChapter}
            totalChapters={totalChapters}
          />

          {/* Milestone 4: Canonical Story Statistics */}
          <StoryMetrics
            totalChaptersVisible={data.total_chapters_visible}
            totalEventsVisible={data.total_events_visible}
            totalCharactersVisible={data.total_characters_visible}
            totalFactionsVisible={data.total_factions_visible}
            totalRelationshipsActive={data.total_relationships_active}
          />

          {/* Milestone 5 & 6: Timeline Preview and Key Turning Points */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: '20px',
              alignItems: 'start',
            }}
          >
            <TimelinePreview
              seriesId={data.series_id}
              readerChapter={readerChapter}
              events={data.recent_events}
            />

            <TurningPointsList
              seriesId={data.series_id}
              readerChapter={readerChapter}
              turningPoints={data.recent_turning_points}
            />
          </div>

          {/* Milestone 7: Character Trajectories */}
          <CharacterRoster
            seriesId={data.series_id}
            readerChapter={readerChapter}
            activePhasesByCharacter={data.active_phases_by_character}
            totalCharacters={data.total_characters_visible}
          />
        </div>
      )}
    </div>
  );
};
