import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';

import {
  useTimelineFeed,
  useStoryOverview,
  useStoryGraph,
  useCharacterArc,
} from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';

import { NarrativeHeader } from '../../features/narrative/components/NarrativeHeader';
import { NarrativePhaseTimeline } from '../../features/narrative/components/NarrativePhaseTimeline';
import { ArcMilestoneTimeline } from '../../features/narrative/components/ArcMilestoneTimeline';
import { TurningPointTimeline } from '../../features/narrative/components/TurningPointTimeline';
import {
  CharacterArcExplorer,
  DiscoveryCharacterItem,
} from '../../features/narrative/components/CharacterArcExplorer';
import {
  NarrativeSelectionSummary,
  SelectedNarrativeEntity,
} from '../../features/narrative/components/NarrativeSelectionSummary';

import {
  adaptArcMilestones,
  adaptTurningPoints,
  adaptCharacterArc,
  FormattedNarrativePhase,
  FormattedArcMilestone,
  FormattedTurningPoint,
} from '../../features/narrative/narrativeAdapters';

import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';

export const NarrativePage: React.FC = () => {
  const { seriesId: routeSeriesId } = useParams<{ seriesId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

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

  // Active Selected Character ID from URL (?characterId=<id>)
  const characterIdFromUrl = searchParams.get('characterId');
  const [selectedCharacterId, setSelectedCharacterId] = useState<string | null>(characterIdFromUrl);

  // Synchronize URL ?chapter=N to TemporalContext
  useEffect(() => {
    const chapterParam = searchParams.get('chapter');
    if (chapterParam) {
      const parsed = parseInt(chapterParam, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed !== readerChapter) {
        setReaderChapter(parsed);
      }
    }
  }, [searchParams, readerChapter, setReaderChapter]);

  // Handle temporal navigation and keep URL in sync
  const handleStepBackward = useCallback(() => {
    if (canStepBackward) {
      stepBackward();
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('chapter', String(Math.max(1, readerChapter - 1)));
          return p;
        },
        { replace: true }
      );
    }
  }, [canStepBackward, stepBackward, readerChapter, setSearchParams]);

  const handleStepForward = useCallback(() => {
    if (canStepForward) {
      stepForward();
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('chapter', String(Math.min(totalChapters, readerChapter + 1)));
          return p;
        },
        { replace: true }
      );
    }
  }, [canStepForward, stepForward, readerChapter, totalChapters, setSearchParams]);

  const handleJumpToStart = useCallback(() => {
    setReaderChapter(1);
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set('chapter', '1');
        return p;
      },
      { replace: true }
    );
  }, [setReaderChapter, setSearchParams]);

  const handleJumpToHorizon = useCallback(() => {
    setReaderChapter(totalChapters);
    setSearchParams(
      (prev) => {
        const p = new URLSearchParams(prev);
        p.set('chapter', String(totalChapters));
        return p;
      },
      { replace: true }
    );
  }, [setReaderChapter, totalChapters, setSearchParams]);

  // Selection state for summary card & inspector
  const [selectedEntity, setSelectedEntity] = useState<SelectedNarrativeEntity | null>(null);

  // 1. Discovery Query: Timeline Feed (provides story milestones & turning points up to readerChapter)
  const timelineQuery = useTimelineFeed(activeSeriesId, readerChapter, { limit: 100 });

  // 2. Discovery Query: Story Overview (provides active phases by character & recent turning points)
  const overviewQuery = useStoryOverview(activeSeriesId, readerChapter);

  // 3. Discovery Query: Generic Graph (provides characters visible at this horizon)
  const graphQuery = useStoryGraph(activeSeriesId, readerChapter, 'relationship');

  // Derive visible characters roster for discovery without fetching any character profiles (0 N+1)
  const visibleCharacters: DiscoveryCharacterItem[] = useMemo(() => {
    if (!graphQuery.data?.nodes) return [];
    const activePhases = overviewQuery.data?.active_phases_by_character || {};

    return graphQuery.data.nodes
      .filter((n) => n.node_type === 'CHARACTER')
      .map((n) => ({
        id: n.id,
        name: n.label,
        activePhaseTitle: activePhases[n.id] || null,
      }))
      .sort((a, b) => a.name.localeCompare(b.name));
  }, [graphQuery.data?.nodes, overviewQuery.data?.active_phases_by_character]);

  // Temporal Firewall Validation: Clear selection if selected character is not visible at readerChapter
  const isCharacterValidAtHorizon = useMemo(() => {
    if (!selectedCharacterId) return false;
    return visibleCharacters.some((c) => c.id === selectedCharacterId);
  }, [selectedCharacterId, visibleCharacters]);

  const activeCharacterId = isCharacterValidAtHorizon ? selectedCharacterId : null;

  // Sync character selection changes to URL
  const handleSelectCharacter = useCallback(
    (charId: string) => {
      setSelectedCharacterId(charId);
      setSearchParams(
        (prev) => {
          const p = new URLSearchParams(prev);
          p.set('characterId', charId);
          return p;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  // Deep Query: Character Arc (strictly gated: executed only when a valid character is selected)
  const arcQuery = useCharacterArc(
    activeSeriesId,
    activeCharacterId,
    readerChapter,
    !!activeCharacterId
  );

  // Purely adapted data
  const adaptedMilestones = useMemo(
    () => adaptArcMilestones(timelineQuery.data?.milestones, readerChapter),
    [timelineQuery.data?.milestones, readerChapter]
  );

  const adaptedTurningPoints = useMemo(() => {
    const rawTps = timelineQuery.data?.turning_points?.length
      ? timelineQuery.data.turning_points
      : overviewQuery.data?.recent_turning_points || [];
    return adaptTurningPoints(rawTps, readerChapter);
  }, [timelineQuery.data?.turning_points, overviewQuery.data?.recent_turning_points, readerChapter]);

  const adaptedCharacterArc = useMemo(
    () => adaptCharacterArc(arcQuery.data, readerChapter),
    [arcQuery.data, readerChapter]
  );

  // Narrative phases: from character arc if selected, otherwise synthesized from character phases
  const adaptedPhases = useMemo(() => {
    if (adaptedCharacterArc?.phases.length) {
      return adaptedCharacterArc.phases;
    }
    // Fallback: derive phase overview from visible character active phases
    const activePhases = overviewQuery.data?.active_phases_by_character || {};
    return Object.entries(activePhases).map(([charId, title], idx) => ({
      id: `phase-${charId}`,
      characterId: charId,
      phaseNumber: idx + 1,
      title,
      fromChapter: 1,
      toChapter: readerChapter,
      milestoneIds: [],
      milestoneCount: 0,
      turningPointId: null,
      dominantFaction: null,
      rankAtPhaseEnd: null,
      isActiveAtHorizon: true,
    }));
  }, [adaptedCharacterArc?.phases, overviewQuery.data?.active_phases_by_character, readerChapter]);

  // Inspector Handlers
  const handleInspectMilestone = useCallback(
    (m: FormattedArcMilestone) => {
      setSelectedEntity({ type: 'MILESTONE', data: m });
      openInspector({
        title: `Milestone: ${m.milestoneType}`,
        subtitle: `Character: ${m.characterId} • Ch. ${m.chapter} (Seq ${m.sequence})`,
        badge: {
          label: m.isCanonical ? 'CANONICAL' : 'ANALYTICAL',
          variant: m.isCanonical ? 'success' : 'neutral',
        },
        content: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Milestone Description
              </span>
              <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{m.description}</p>
            </div>

            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                State Transition Details
              </span>
              <div
                style={{
                  marginTop: '6px',
                  padding: '10px 12px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  borderRadius: 'var(--tsi-radius-md)',
                  fontFamily: 'var(--tsi-font-mono)',
                  fontSize: '0.75rem',
                }}
              >
                <div>Previous: {JSON.stringify(m.previousState)}</div>
                <div style={{ color: 'var(--tsi-accent-primary)', marginTop: '4px' }}>
                  New: {JSON.stringify(m.newState)}
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                size="sm"
                variant="primary"
                onClick={() => navigate(`/series/${activeSeriesId}/characters/${encodeURIComponent(m.characterId)}`)}
              >
                Character Profile ↗
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => navigate(`/series/${activeSeriesId}/timeline`)}
              >
                Find in Timeline ↗
              </Button>
            </div>
          </div>
        ),
      });
    },
    [activeSeriesId, navigate, openInspector]
  );

  const handleInspectTurningPoint = useCallback(
    (tp: FormattedTurningPoint) => {
      setSelectedEntity({ type: 'TURNING_POINT', data: tp });
      openInspector({
        title: `${tp.turningPointType.replace(/_/g, ' ')} Turning Point`,
        subtitle: `Character: ${tp.characterId} • Chapter ${tp.chapter}`,
        badge: {
          label: tp.significance.toUpperCase(),
          variant: tp.significance.toUpperCase() === 'CRITICAL' ? 'error' : 'warning',
        },
        content: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Significance & Event
              </span>
              <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>
                {tp.significance.toUpperCase()} • Event: {tp.eventId}
              </p>
            </div>

            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Description
              </span>
              <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{tp.description}</p>
            </div>

            {tp.affectedDimensions.length > 0 && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Affected Dimensions
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '4px' }}>
                  {tp.affectedDimensions.map((dim) => (
                    <Badge key={dim} variant="neutral" style={{ fontSize: '0.6875rem' }}>
                      {dim}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Resulting State Delta
              </span>
              <pre
                style={{
                  margin: '4px 0 0',
                  padding: '8px 10px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  borderRadius: 'var(--tsi-radius-md)',
                  fontSize: '0.75rem',
                  fontFamily: 'var(--tsi-font-mono)',
                  overflowX: 'auto',
                }}
              >
                {JSON.stringify(tp.resultingState, null, 2)}
              </pre>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <Button
                size="sm"
                variant="primary"
                onClick={() => navigate(`/series/${activeSeriesId}/causality`)}
              >
                Investigate Causality ↗
              </Button>
            </div>
          </div>
        ),
      });
    },
    [activeSeriesId, navigate, openInspector]
  );

  const handleInspectPhase = useCallback(
    (phase: FormattedNarrativePhase) => {
      setSelectedEntity({ type: 'PHASE', data: phase });
      openInspector({
        title: `Phase ${phase.phaseNumber}: ${phase.title}`,
        subtitle: `Character: ${phase.characterId} • Chapters ${phase.fromChapter} – ${phase.toChapter}`,
        badge: {
          label: phase.isActiveAtHorizon ? 'ACTIVE HORIZON' : 'HISTORICAL',
          variant: phase.isActiveAtHorizon ? 'temporal' : 'neutral',
        },
        content: (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.875rem' }}>
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Phase Span
              </span>
              <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>
                Spans Chapter {phase.fromChapter} to {phase.toChapter} ({phase.milestoneCount} milestones)
              </p>
            </div>

            {phase.dominantFaction && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Dominant Faction
                </span>
                <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{phase.dominantFaction}</p>
              </div>
            )}

            {phase.rankAtPhaseEnd && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Terminal Rank
                </span>
                <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{phase.rankAtPhaseEnd}</p>
              </div>
            )}

            <Button
              size="sm"
              variant="primary"
              onClick={() => navigate(`/series/${activeSeriesId}/characters/${encodeURIComponent(phase.characterId)}`)}
            >
              Inspect Character Profile ↗
            </Button>
          </div>
        ),
      });
    },
    [activeSeriesId, navigate, openInspector]
  );

  const selectedCharName = visibleCharacters.find((c) => c.id === activeCharacterId)?.name;

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '20px',
        padding: '24px 32px',
        maxWidth: '1540px',
        margin: '0 auto',
        width: '100%',
      }}
    >
      {/* Narrative Header */}
      <NarrativeHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        totalPhasesVisible={adaptedPhases.length}
        totalMilestonesVisible={adaptedMilestones.length}
        totalTurningPointsVisible={adaptedTurningPoints.length}
        selectedCharacterName={selectedCharName}
        onJumpToStart={handleJumpToStart}
        onStepBackward={handleStepBackward}
        onStepForward={handleStepForward}
        onJumpToHorizon={handleJumpToHorizon}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Loading Skeleton */}
      {timelineQuery.isLoading && overviewQuery.isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Skeleton height={140} borderRadius="var(--tsi-radius-lg)" />
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
            <Skeleton height={320} borderRadius="var(--tsi-radius-lg)" />
            <Skeleton height={320} borderRadius="var(--tsi-radius-lg)" />
          </div>
        </div>
      )}

      {/* Error State */}
      {(timelineQuery.isError || overviewQuery.isError) && (
        <ErrorState
          title="Narrative Intelligence Query Failed"
          message={
            timelineQuery.error?.message ||
            overviewQuery.error?.message ||
            'Unable to load narrative intelligence read model.'
          }
          status={timelineQuery.error?.status || overviewQuery.error?.status}
          onRetry={() => {
            timelineQuery.refetch();
            overviewQuery.refetch();
          }}
        />
      )}

      {/* Populated Narrative Workspace */}
      {(!timelineQuery.isLoading || !overviewQuery.isLoading) && (
        <>
          {/* 1. Narrative Phases Progression */}
          <NarrativePhaseTimeline
            phases={adaptedPhases}
            readerChapter={readerChapter}
            onSelectPhase={handleInspectPhase}
          />

          {/* 2. Side-by-side: Arc Milestones & Turning Points */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))',
              gap: '20px',
              alignItems: 'start',
            }}
          >
            <ArcMilestoneTimeline
              milestones={adaptedMilestones}
              readerChapter={readerChapter}
              onInspectMilestone={handleInspectMilestone}
            />

            <TurningPointTimeline
              turningPoints={adaptedTurningPoints}
              readerChapter={readerChapter}
              onInspectTurningPoint={handleInspectTurningPoint}
            />
          </div>

          {/* 3. Character Arc Explorer (On-Demand Deep Arc) */}
          <CharacterArcExplorer
            characters={visibleCharacters}
            selectedCharacterId={activeCharacterId}
            onSelectCharacter={handleSelectCharacter}
            arcData={adaptedCharacterArc}
            isLoadingArc={arcQuery.isLoading}
            readerChapter={readerChapter}
            onInspectMilestone={handleInspectMilestone}
            onInspectTurningPoint={handleInspectTurningPoint}
            onInspectPhase={handleInspectPhase}
          />

          {/* 4. Selection Summary Bar */}
          <NarrativeSelectionSummary
            selection={selectedEntity}
            seriesId={activeSeriesId}
            readerChapter={readerChapter}
            onOpenInspector={() => {
              if (selectedEntity) {
                if (selectedEntity.type === 'MILESTONE') handleInspectMilestone(selectedEntity.data);
                else if (selectedEntity.type === 'TURNING_POINT') handleInspectTurningPoint(selectedEntity.data);
                else if (selectedEntity.type === 'PHASE') handleInspectPhase(selectedEntity.data);
              }
            }}
            onNavigateToCharacter={(cId) => navigate(`/series/${activeSeriesId}/characters/${encodeURIComponent(cId)}`)}
            onNavigateToTimeline={() => navigate(`/series/${activeSeriesId}/timeline`)}
            onClearSelection={() => setSelectedEntity(null)}
          />
        </>
      )}
    </div>
  );
};
