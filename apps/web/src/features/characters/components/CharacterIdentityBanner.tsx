import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { CharacterReadModel } from '../../../api/contracts/read-models';

export interface CharacterIdentityBannerProps {
  seriesId: string;
  readerChapter: number;
  character: CharacterReadModel;
  onOpenInspector: () => void;
}

export const CharacterIdentityBanner: React.FC<CharacterIdentityBannerProps> = ({
  seriesId,
  readerChapter,
  character,
  onOpenInspector,
}) => {
  const isDead = character.status === 'dead';
  const isUnintroduced = character.status === 'unintroduced';

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        padding: '24px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-lg)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top accent border */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '4px',
          backgroundColor: isDead ? 'var(--tsi-danger-default)' : 'var(--tsi-accent-primary)',
        }}
      />

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'flex-start',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <Link
              to={`/series/${encodeURIComponent(seriesId)}/characters`}
              style={{
                fontSize: '0.8125rem',
                color: 'var(--tsi-accent-primary)',
                textDecoration: 'none',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                marginRight: '8px',
              }}
            >
              ← All Characters
            </Link>
            <Badge variant="neutral" style={{ fontFamily: 'var(--tsi-font-mono)', fontSize: '0.6875rem' }}>
              ID: {character.character_id}
            </Badge>
            <Badge
              variant={isDead ? 'error' : isUnintroduced ? 'neutral' : 'success'}
              style={{ fontSize: '0.6875rem', textTransform: 'uppercase' }}
            >
              {character.status.toUpperCase()}
            </Badge>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: '2rem',
              fontWeight: 700,
              color: 'var(--tsi-text-primary)',
              letterSpacing: '-0.025em',
            }}
          >
            {character.name}
          </h1>

          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginTop: '2px' }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Active Narrative Phase:
            </span>
            <span style={{ fontSize: '0.9375rem', fontWeight: 600, color: 'var(--tsi-accent-primary)' }}>
              {character.current_phase_title || 'Genesis Arc Phase'}
            </span>
          </div>
        </div>

        {/* Quick Inspector & Graph Actions */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
          <Button
            size="sm"
            variant="secondary"
            onClick={onOpenInspector}
            aria-label="Inspect character metadata drawer"
          >
            Inspect Drawer 🔍
          </Button>
          <Link
            to={`/series/${encodeURIComponent(seriesId)}/graph`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '6px 12px',
              fontSize: '0.8125rem',
              fontWeight: 500,
              color: 'var(--tsi-text-primary)',
              backgroundColor: 'var(--tsi-surface-secondary)',
              border: '1px solid var(--tsi-border-default)',
              borderRadius: 'var(--tsi-radius-md)',
              textDecoration: 'none',
            }}
          >
            Relationship Graph ⚯
          </Link>
          <Link
            to={`/series/${encodeURIComponent(seriesId)}/causality`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              padding: '6px 12px',
              fontSize: '0.8125rem',
              fontWeight: 500,
              color: 'var(--tsi-text-primary)',
              backgroundColor: 'var(--tsi-surface-secondary)',
              border: '1px solid var(--tsi-border-default)',
              borderRadius: 'var(--tsi-radius-md)',
              textDecoration: 'none',
            }}
          >
            Causal Chains ↯
          </Link>
        </div>
      </div>

      {/* Trajectory Metrics Bar */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '10px',
          paddingTop: '16px',
          borderTop: '1px solid var(--tsi-border-subtle)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Power Rank
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {character.rank || 'Unranked'}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Faction Affiliation
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {character.faction_id || 'Unaligned'}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Milestones Reached
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {character.total_milestones_reached}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Turning Points Passed
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-temporal-scope)' }}>
            {character.total_turning_points_passed}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Active Relationships
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {character.active_relationships_count}
          </span>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Unlocked Skills
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            {character.unlocked_skills.length}
          </span>
        </div>
      </div>
    </div>
  );
};
