import React from 'react';
import { Link } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export interface CharacterItemSummary {
  characterId: string;
  name: string;
  currentPhaseTitle?: string | null;
  status?: 'alive' | 'dead' | 'unintroduced' | string;
  rank?: string | null;
  factionId?: string | null;
}

export interface CharacterCardProps {
  seriesId: string;
  readerChapter: number;
  character: CharacterItemSummary;
  onInspect: (character: CharacterItemSummary) => void;
}

export const CharacterCard: React.FC<CharacterCardProps> = ({
  seriesId,
  readerChapter,
  character,
  onInspect,
}) => {
  const isDead = character.status === 'dead';
  const isUnintroduced = character.status === 'unintroduced';

  return (
    <Card
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        gap: '14px',
        padding: '16px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
        transition: 'all 0.15s ease',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
          <div>
            <Link
              to={`/series/${encodeURIComponent(seriesId)}/characters/${encodeURIComponent(character.characterId)}`}
              style={{
                fontSize: '1rem',
                fontWeight: 600,
                color: 'var(--tsi-text-primary)',
                textDecoration: 'none',
                lineHeight: 1.3,
                display: 'inline-block',
              }}
              title={`View character profile for ${character.name}`}
            >
              {character.name}
            </Link>
            <div style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', fontFamily: 'var(--tsi-font-mono)' }}>
              ID: {character.characterId}
            </div>
          </div>

          <Badge
            variant={isDead ? 'error' : isUnintroduced ? 'neutral' : 'success'}
            style={{ fontSize: '0.625rem', textTransform: 'uppercase' }}
          >
            {character.status ? character.status.toUpperCase() : 'ACTIVE'}
          </Badge>
        </div>

        {/* Narrative Phase Trajectory */}
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Current Phase:
          </span>
          <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--tsi-accent-primary)' }}>
            {character.currentPhaseTitle || 'Genesis Arc'}
          </span>
        </div>

        {/* State metadata chips (rank, faction if provided) */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
          {character.rank && (
            <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
              Rank: {character.rank}
            </Badge>
          )}
          {character.factionId && (
            <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
              Faction: {character.factionId}
            </Badge>
          )}
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            Ch. {readerChapter} Horizon
          </Badge>
        </div>
      </div>

      {/* Action Footer with Semantic Link + Inspect Button */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '8px',
          paddingTop: '10px',
          borderTop: '1px solid var(--tsi-border-subtle)',
        }}
      >
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onInspect(character)}
          aria-label={`Inspect summary for ${character.name}`}
          style={{ fontSize: '0.75rem', padding: '4px 8px' }}
        >
          Quick Inspect 🔍
        </Button>

        <Link
          to={`/series/${encodeURIComponent(seriesId)}/characters/${encodeURIComponent(character.characterId)}`}
          style={{
            fontSize: '0.75rem',
            fontWeight: 600,
            color: 'var(--tsi-accent-primary)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '4px',
          }}
        >
          Full Intelligence Profile →
        </Link>
      </div>
    </Card>
  );
};
