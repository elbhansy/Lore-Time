import React, { useState, useMemo } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { useStoryOverview, useStoryGraph } from '../../features/temporal/queries/useIntelligenceQueries';
import { useTemporalContext } from '../../state/temporal/temporal-context';
import { useShellContext } from '../../state/shell/shell-context';
import { CharacterExplorerHeader } from '../../features/characters/components/CharacterExplorerHeader';
import { CharacterCard, CharacterItemSummary } from '../../features/characters/components/CharacterCard';
import { Skeleton } from '../../components/feedback/Skeleton';
import { ErrorState } from '../../components/feedback/ErrorState';
import { EmptyState } from '../../components/feedback/EmptyState';
import { Badge } from '../../components/ui/Badge';
import { Link } from 'react-router-dom';

export const CharactersPage: React.FC = () => {
  const { seriesId: routeSeriesId } = useParams<{ seriesId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
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
  const [searchQuery, setSearchQuery] = useState('');

  // Sync URL ?chapter=N to TemporalContext
  React.useEffect(() => {
    const chapterParam = searchParams.get('chapter');
    if (chapterParam) {
      const parsed = parseInt(chapterParam, 10);
      if (!isNaN(parsed) && parsed >= 1 && parsed !== readerChapter) {
        setReaderChapter(parsed);
      }
    }
  }, [searchParams, readerChapter, setReaderChapter]);

  // Primary lightweight collection queries (Overview + Relationship Graph)
  // Story overview provides active_phases_by_character and total_characters_visible
  const overviewQuery = useStoryOverview(activeSeriesId, readerChapter);
  // Relationship graph provides all visible character IDs and friendly display names
  const graphQuery = useStoryGraph(activeSeriesId, readerChapter, 'relationship');

  const isLoading = overviewQuery.isLoading || graphQuery.isLoading;
  const isError = overviewQuery.isError || graphQuery.isError;
  const error = overviewQuery.error || graphQuery.error;

  // Build lightweight character roster strictly without N+1 profile fetching
  const visibleCharacters: CharacterItemSummary[] = useMemo(() => {
    if (!graphQuery.data?.nodes && !overviewQuery.data?.active_phases_by_character) {
      return [];
    }

    const phaseMap = overviewQuery.data?.active_phases_by_character || {};
    const nodes = graphQuery.data?.nodes || [];

    // Filter nodes for CHARACTER node_type
    const charNodes = nodes.filter((n) => n.node_type === 'CHARACTER');

    const result: CharacterItemSummary[] = [];
    const seenIds = new Set<string>();

    for (const node of charNodes) {
      if (!seenIds.has(node.id)) {
        seenIds.add(node.id);
        result.push({
          characterId: node.id,
          name: node.label || node.id,
          currentPhaseTitle: phaseMap[node.id] || null,
          status: 'alive',
        });
      }
    }

    // Include any characters that have active phases but weren't in graph nodes
    for (const [charId, phaseTitle] of Object.entries(phaseMap)) {
      if (!seenIds.has(charId)) {
        seenIds.add(charId);
        result.push({
          characterId: charId,
          name: charId,
          currentPhaseTitle: phaseTitle,
          status: 'alive',
        });
      }
    }

    // Sort alphabetically by name
    return result.sort((a, b) => a.name.localeCompare(b.name));
  }, [graphQuery.data?.nodes, overviewQuery.data?.active_phases_by_character]);

  // Filter by search query
  const filteredCharacters = useMemo(() => {
    if (!searchQuery.trim()) return visibleCharacters;
    const q = searchQuery.toLowerCase();
    return visibleCharacters.filter(
      (c) => c.name.toLowerCase().includes(q) || c.characterId.toLowerCase().includes(q)
    );
  }, [visibleCharacters, searchQuery]);

  // Inspector quick-action integration
  const handleInspectCharacter = (char: CharacterItemSummary) => {
    openInspector({
      title: char.name,
      subtitle: `Character Identifier: ${char.characterId}`,
      badge: {
        label: `CH. ${readerChapter} HORIZON`,
        variant: 'temporal',
      },
      content: (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', fontSize: '0.875rem' }}>
          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Current Narrative Phase
            </span>
            <p style={{ margin: '4px 0 0', fontWeight: 600, color: 'var(--tsi-accent-primary)' }}>
              {char.currentPhaseTitle || 'Genesis Arc Phase'}
            </p>
          </div>

          <div>
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Temporal Horizon
            </span>
            <p style={{ margin: '4px 0 0', color: 'var(--tsi-text-secondary)' }}>
              Known up through Chapter {readerChapter}. Deep intelligence reflects strictly verified facts.
            </p>
          </div>

          <div style={{ paddingTop: '8px' }}>
            <Link
              to={`/series/${encodeURIComponent(activeSeriesId)}/characters/${encodeURIComponent(char.characterId)}`}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                padding: '8px 14px',
                fontSize: '0.8125rem',
                fontWeight: 600,
                color: 'white',
                backgroundColor: 'var(--tsi-accent-primary)',
                borderRadius: 'var(--tsi-radius-md)',
                textDecoration: 'none',
              }}
            >
              Open Full Intelligence Profile →
            </Link>
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
        maxWidth: '1440px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box',
      }}
    >
      {/* Header with Search and Temporal Steppers */}
      <CharacterExplorerHeader
        seriesId={activeSeriesId}
        readerChapter={readerChapter}
        totalChapters={totalChapters}
        totalVisibleCharacters={filteredCharacters.length}
        searchQuery={searchQuery}
        onSearchChange={setSearchQuery}
        onJumpToStart={() => {
          setReaderChapter(1);
          setSearchParams({ chapter: '1' });
        }}
        onStepBackward={() => {
          if (canStepBackward) {
            stepBackward();
            setSearchParams({ chapter: String(Math.max(1, readerChapter - 1)) });
          }
        }}
        onStepForward={() => {
          if (canStepForward) {
            stepForward();
            setSearchParams({ chapter: String(readerChapter + 1) });
          }
        }}
        onJumpToHorizon={() => {
          setReaderChapter(totalChapters);
          setSearchParams({ chapter: String(totalChapters) });
        }}
        canStepBackward={canStepBackward}
        canStepForward={canStepForward}
      />

      {/* Loading Skeleton */}
      {isLoading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
          <Skeleton height={160} borderRadius="var(--tsi-radius-md)" />
        </div>
      )}

      {/* Error State */}
      {isError && (
        <ErrorState
          title="Failed to Load Characters"
          message={error?.message || 'Unable to retrieve characters for this temporal horizon.'}
          status={error?.status}
          onRetry={() => {
            overviewQuery.refetch();
            graphQuery.refetch();
          }}
        />
      )}

      {/* Empty State */}
      {!isLoading && !isError && filteredCharacters.length === 0 && (
        <EmptyState
          title={searchQuery ? 'No Matching Characters Found' : 'No Characters Discovered Yet'}
          description={
            searchQuery
              ? `No character in Chapter 1 through ${readerChapter} matches "${searchQuery}".`
              : `No characters have been introduced as of Chapter ${readerChapter}.`
          }
        />
      )}

      {/* Populated Character Cards Grid */}
      {!isLoading && !isError && filteredCharacters.length > 0 && (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(290px, 1fr))',
            gap: '16px',
          }}
        >
          {filteredCharacters.map((char) => (
            <CharacterCard
              key={char.characterId}
              seriesId={activeSeriesId}
              readerChapter={readerChapter}
              character={char}
              onInspect={handleInspectCharacter}
            />
          ))}
        </div>
      )}
    </div>
  );
};
