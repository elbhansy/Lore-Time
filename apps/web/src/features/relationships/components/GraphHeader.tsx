import React from 'react';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export interface GraphHeaderProps {
  seriesId: string;
  readerChapter: number;
  totalChapters?: number;
  characterCount: number;
  relationshipCount: number;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onJumpToStart?: () => void;
  onStepBackward?: () => void;
  onStepForward?: () => void;
  onJumpToHorizon?: () => void;
  onResetView?: () => void;
  canStepBackward?: boolean;
  canStepForward?: boolean;
}

export const GraphHeader: React.FC<GraphHeaderProps> = ({
  seriesId: _seriesId,
  readerChapter,
  totalChapters = 200,
  characterCount,
  relationshipCount,
  searchQuery,
  onSearchChange,
  onJumpToStart,
  onStepBackward,
  onStepForward,
  onJumpToHorizon,
  onResetView,
  canStepBackward = true,
  canStepForward = true,
}) => {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '18px 24px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-lg)',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      {/* Top subtle boundary glow */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '3px',
          backgroundColor: 'var(--tsi-accent-primary)',
        }}
      />

      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h1
              style={{
                margin: 0,
                fontSize: '1.5rem',
                fontWeight: 700,
                color: 'var(--tsi-text-primary)',
                letterSpacing: '-0.02em',
              }}
            >
              Relationship Graph Intelligence
            </h1>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>

          <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
            Universal topology of active relationships, allegiances, and bonds.
            Displaying {characterCount} characters and {relationshipCount} directed relationships as of Chapter {readerChapter}.
          </p>
        </div>

        {/* Temporal Stepper Controls */}
        <div
          role="group"
          aria-label="Graph Horizon Controls"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            backgroundColor: 'var(--tsi-surface-secondary)',
            border: '1px solid var(--tsi-border-default)',
            borderRadius: 'var(--tsi-radius-md)',
            padding: '4px 8px',
          }}
        >
          <span
            style={{
              fontSize: '0.6875rem',
              color: 'var(--tsi-text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              paddingRight: '4px',
            }}
          >
            Reader Horizon:
          </span>

          {onJumpToStart && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onJumpToStart}
              disabled={!canStepBackward}
              title="Jump to Chapter 1"
              aria-label="Jump to Chapter 1"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              |◀
            </Button>
          )}

          {onStepBackward && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onStepBackward}
              disabled={!canStepBackward}
              title="Step backward one chapter"
              aria-label="Step backward one chapter"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              ◀
            </Button>
          )}

          <div style={{ padding: '0 6px', display: 'flex', alignItems: 'baseline', gap: '3px' }}>
            <span style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'var(--tsi-text-primary)' }}>
              Ch. {readerChapter}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
              / {totalChapters}
            </span>
          </div>

          {onStepForward && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onStepForward}
              disabled={!canStepForward}
              title="Step forward one chapter"
              aria-label="Step forward one chapter"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              ▶
            </Button>
          )}

          {onJumpToHorizon && (
            <Button
              size="sm"
              variant="ghost"
              onClick={onJumpToHorizon}
              disabled={!canStepForward}
              title="Jump to max chapter"
              aria-label="Jump to max chapter"
              style={{ padding: '2px 6px', fontSize: '0.75rem' }}
            >
              ▶|
            </Button>
          )}
        </div>
      </div>

      {/* Graph Toolbar with Search and Reset Fit */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px', flexWrap: 'wrap' }}>
        <div style={{ position: 'relative', flex: 1, maxWidth: '320px' }}>
          <input
            type="text"
            role="searchbox"
            aria-label="Filter characters in graph"
            placeholder="Focus character in graph..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            style={{
              width: '100%',
              padding: '6px 12px',
              backgroundColor: 'var(--tsi-surface-secondary)',
              border: '1px solid var(--tsi-border-default)',
              borderRadius: 'var(--tsi-radius-md)',
              color: 'var(--tsi-text-primary)',
              fontSize: '0.8125rem',
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          {searchQuery && (
            <button
              onClick={() => onSearchChange('')}
              aria-label="Clear graph filter"
              style={{
                position: 'absolute',
                right: '8px',
                top: '50%',
                transform: 'translateY(-50%)',
                background: 'transparent',
                border: 'none',
                color: 'var(--tsi-text-muted)',
                cursor: 'pointer',
                fontSize: '0.8125rem',
              }}
            >
              ✕
            </button>
          )}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="neutral" data-testid="graph-character-count-badge">
            {characterCount} {characterCount === 1 ? 'Character' : 'Characters'}
          </Badge>
          <Badge variant="neutral" data-testid="graph-relationship-count-badge">
            {relationshipCount} {relationshipCount === 1 ? 'Relationship' : 'Relationships'}
          </Badge>

          {onResetView && (
            <Button
              size="sm"
              variant="secondary"
              onClick={onResetView}
              aria-label="Fit graph view"
              style={{ fontSize: '0.75rem', padding: '4px 10px' }}
            >
              Fit View ⤢
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
