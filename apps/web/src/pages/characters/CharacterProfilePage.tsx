import React, { useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import {
  useCharacterProfile,
  useCharacterNarrativeCausality,
} from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { CharacterIdentityBanner } from '../../features/characters/components/CharacterIdentityBanner';
import { CharacterArcSection } from '../../features/characters/components/CharacterArcSection';
import { CharacterTurningPointsSection } from '../../features/characters/components/CharacterTurningPointsSection';
import { CharacterCausalitySection } from '../../features/characters/components/CharacterCausalitySection';
import { CharacterSynthesisSection } from '../../features/characters/components/CharacterSynthesisSection';
import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { ArcMilestoneDTO, TurningPointDTO, NarrativeCausalStepDTO } from '../../api/contracts/read-models';

export const CharacterProfilePage: React.FC = () => {
  const { seriesId: routeSeriesId, characterId = '' } = useParams<{ seriesId: string; characterId: string }>();
  const [searchParams] = useSearchParams();
  const {
    seriesId: contextSeriesId,
    readerChapter,
    setReaderChapter,
  } = useTemporalContext();

  const activeSeriesId = routeSeriesId || contextSeriesId;
  const { openInspector } = useShellContext();

  // Sync URL ?chapter=N to TemporalContext
  useEffect(() => {
    const chapterParam = searchParams.get('chapter');
    if (chapterParam) {
      const parsed = parseInt(chapterParam, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed !== readerChapter) {
        setReaderChapter(parsed);
      }
    }
  }, [searchParams, readerChapter, setReaderChapter]);

  // Query 1: Full Character Read Model at readerChapter
  const profileQuery = useCharacterProfile(activeSeriesId, characterId, readerChapter);

  // Query 2: Deterministic Causal Narrative Synthesis for this Character
  const causalityQuery = useCharacterNarrativeCausality(activeSeriesId, characterId, readerChapter, 4);

  const isLoading = profileQuery.isLoading;
  const isError = profileQuery.isError;
  const character = profileQuery.data;

  // Context Inspector for Milestone
  const handleInspectMilestone = (m: ArcMilestoneDTO) => {
    openInspector({
      title: `Milestone: ${m.milestone_type}`,
      subtitle: `Character: ${character?.name || characterId} • Ch. ${m.chapter}`,
      badge: {
        label: m.is_canonical ? 'CANONICAL' : 'ANALYTICAL',
        variant: m.is_canonical ? 'success' : 'neutral',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Description
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{m.description}</p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              State Delta
            </span>
            <div style={{ marginTop: '6px', fontSize: '0.75rem', fontFamily: 'var(--tsi-font-mono)' }}>
              <div>Prev: {JSON.stringify(m.previous_state)}</div>
              <div style={{ color: 'var(--tsi-accent-primary)' }}>New: {JSON.stringify(m.new_state)}</div>
            </div>
          </div>
        </div>
      ),
    });
  };

  // Context Inspector for Turning Point
  const handleInspectTurningPoint = (tp: TurningPointDTO) => {
    openInspector({
      title: `${tp.turning_point_type} Turning Point`,
      subtitle: `Character: ${character?.name || characterId} • Ch. ${tp.chapter}`,
      badge: {
        label: tp.significance.toUpperCase(),
        variant: tp.significance === 'high' || tp.significance === 'critical' ? 'warning' : 'temporal',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Significance & Type
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>
              {tp.significance.toUpperCase()} • {tp.turning_point_type}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Description
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>{tp.description}</p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Resulting State
            </span>
            <pre style={{ margin: '4px 0 0', fontSize: '0.75rem', fontFamily: 'var(--tsi-font-mono)', overflowX: 'auto' }}>
              {JSON.stringify(tp.resulting_state, null, 2)}
            </pre>
          </div>
        </div>
      ),
    });
  };

  // Context Inspector for Causal Step
  const handleInspectCausalStep = (step: NarrativeCausalStepDTO) => {
    openInspector({
      title: `Causal Step: ${step.relation_type}`,
      subtitle: `Ch. ${step.chapter} • Confidence: ${step.confidence}`,
      badge: {
        label: step.derivation_type,
        variant: 'neutral',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              State Change Summary
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-primary)' }}>
              {step.state_change_summary || 'No state change recorded'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Affected Entities
            </span>
            <p style={{ margin: '4px 0 0', fontFamily: 'var(--tsi-font-mono)' }}>
              {step.affected_entities.join(', ') || 'None'}
            </p>
          </div>

          {step.impact_dimensions.length > 0 && (
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Impact Dimensions
              </span>
              <p style={{ margin: '4px 0 0' }}>{step.impact_dimensions.join(', ')}</p>
            </div>
          )}
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
        boxSizing: 'border-box',
      }}
    >
      {/* Loading Skeleton */}
      {isLoading && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <Skeleton height={200} borderRadius="var(--tsi-radius-lg)" />
          <Skeleton height={280} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={240} borderRadius="var(--tsi-radius-md)" />
        </div>
      )}

      {/* Error State */}
      {isError && (
        <ErrorState
          title="Character Not Found"
          message={profileQuery.error?.message || 'Unable to retrieve character read model for this horizon.'}
          status={profileQuery.error?.status}
          onRetry={() => {
            profileQuery.refetch();
            causalityQuery.refetch();
          }}
        />
      )}

      {/* Temporal Firewall Guard: Unintroduced Character */}
      {!isLoading && !isError && character && character.status === 'unintroduced' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <Link
            to={`/series/${encodeURIComponent(activeSeriesId)}/characters`}
            style={{ fontSize: '0.875rem', color: 'var(--tsi-accent-primary)', textDecoration: 'none' }}
          >
            ← Back to Character Explorer
          </Link>
          <EmptyState
            title="Character Not Introduced (Spoiler Firewall)"
            description={`This character has not been introduced as of Chapter ${readerChapter}. Future state and arc events are shielded.`}
          />
        </div>
      )}

      {/* Populated Profile Workspace */}
      {!isLoading && !isError && character && character.status !== 'unintroduced' && (
        <>
          {/* Identity & Current Temporal State Banner */}
          <CharacterIdentityBanner
            seriesId={activeSeriesId}
            readerChapter={readerChapter}
            character={character}
            onOpenInspector={() => {
              openInspector({
                title: character.name,
                subtitle: `Full Record: ${character.character_id}`,
                badge: {
                  label: character.status.toUpperCase(),
                  variant: character.status === 'alive' ? 'success' : 'error',
                },
                content: (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '0.875rem' }}>
                    <div>
                      <strong>Power Rank:</strong> {character.rank || 'Unranked'}
                    </div>
                    <div>
                      <strong>Faction:</strong> {character.faction_id || 'None'}
                    </div>
                    <div>
                      <strong>Active Skills:</strong>{' '}
                      {character.unlocked_skills.length > 0
                        ? character.unlocked_skills.join(', ')
                        : 'None unlocked'}
                    </div>
                    <div>
                      <strong>Relationships Count:</strong> {character.active_relationships_count}
                    </div>
                  </div>
                ),
              });
            }}
          />

          {/* Narrative Synthesis Section */}
          <CharacterSynthesisSection
            synthesis={causalityQuery.data}
            readerChapter={readerChapter}
          />

          {/* Character Arc & Narrative Phases Section */}
          <CharacterArcSection
            phases={character.phases}
            milestones={character.milestones}
            readerChapter={readerChapter}
            onInspectMilestone={handleInspectMilestone}
          />

          {/* Authoritative Turning Points Section */}
          <CharacterTurningPointsSection
            turningPoints={character.turning_points}
            readerChapter={readerChapter}
            onInspectTurningPoint={handleInspectTurningPoint}
          />

          {/* Causal History & Propagation Section */}
          <CharacterCausalitySection
            synthesis={causalityQuery.data}
            readerChapter={readerChapter}
            onInspectStep={handleInspectCausalStep}
          />
        </>
      )}
    </div>
  );
};
