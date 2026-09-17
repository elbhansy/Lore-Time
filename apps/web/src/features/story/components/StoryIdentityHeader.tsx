import React from 'react';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { useNavigate } from 'react-router-dom';

export interface StoryIdentityHeaderProps {
  seriesId: string;
  seriesTitle: string;
  readerChapter: number;
  totalChapters?: number;
}

export const StoryIdentityHeader: React.FC<StoryIdentityHeaderProps> = ({
  seriesId,
  seriesTitle,
  readerChapter,
  totalChapters = 200,
}) => {
  const navigate = useNavigate();

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
      {/* Decorative subtle border line */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '2px',
          background: 'linear-gradient(90deg, var(--tsi-accent-primary) 0%, transparent 80%)',
        }}
      />

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Badge variant="neutral" style={{ textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Series Investigation
            </Badge>
            <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)', fontFamily: 'var(--tsi-font-mono)' }}>
              ID: {seriesId}
            </span>
          </div>

          <h1
            style={{
              margin: 0,
              fontSize: '1.875rem',
              fontWeight: 700,
              color: 'var(--tsi-text-primary)',
              letterSpacing: '-0.025em',
              lineHeight: 1.2,
            }}
          >
            {seriesTitle || 'Canonical Story Overview'}
          </h1>

          <p style={{ margin: 0, fontSize: '0.9375rem', color: 'var(--tsi-text-secondary)', maxWidth: '640px' }}>
            Interactive story intelligence dashboard synthesized up to the reader&apos;s current knowledge horizon.
            All turning points, relationships, and events reflect strictly verified canonical facts without future leakage.
          </p>
        </div>

        {/* Temporal Horizon Card */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '6px',
            backgroundColor: 'var(--tsi-surface-secondary)',
            border: '1px solid var(--tsi-border-default)',
            borderRadius: 'var(--tsi-radius-md)',
            padding: '12px 18px',
            minWidth: '220px',
          }}
        >
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Temporal Horizon
          </span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
            <span style={{ fontSize: '1.75rem', fontWeight: 700, color: 'var(--tsi-temporal-scope)' }}>
              Ch. {readerChapter}
            </span>
            <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)' }}>
              / {totalChapters} total
            </span>
          </div>
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            Known Through Chapter {readerChapter}
          </Badge>
        </div>
      </div>

      {/* Investigation Action Shortcuts */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          gap: '8px',
          paddingTop: '8px',
          borderTop: '1px solid var(--tsi-border-subtle)',
        }}
      >
        <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginRight: '4px' }}>
          Explore:
        </span>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/series/${seriesId}/timeline`)}
          title="Open Chronological Timeline Feed"
        >
          ◷ Timeline Feed
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/series/${seriesId}/characters`)}
          title="Open Character Intelligence Directory"
        >
          ♟ Characters
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/series/${seriesId}/graph`)}
          title="Open Universal Intelligence Graph"
        >
          ⚯ Intelligence Graph
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => navigate(`/series/${seriesId}/causality`)}
          title="Open Deterministic Causal Chains"
        >
          ↯ Causal Chains
        </Button>
      </div>
    </div>
  );
};
