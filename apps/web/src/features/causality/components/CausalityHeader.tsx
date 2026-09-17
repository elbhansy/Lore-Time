import React from 'react';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export interface CausalityHeaderProps {
  seriesId: string;
  readerChapter: number;
  totalChapters?: number;
  activeMode: 'EVENT' | 'CHARACTER';
  targetTitle?: string | null;
  nodeCount: number;
  edgeCount: number;
  onJumpToStart?: () => void;
  onStepBackward?: () => void;
  onStepForward?: () => void;
  onJumpToHorizon?: () => void;
  canStepBackward?: boolean;
  canStepForward?: boolean;
}

export const CausalityHeader: React.FC<CausalityHeaderProps> = ({
  seriesId: _seriesId,
  readerChapter,
  totalChapters = 200,
  activeMode,
  targetTitle,
  nodeCount,
  edgeCount,
  onJumpToStart,
  onStepBackward,
  onStepForward,
  onJumpToHorizon,
  canStepBackward = true,
  canStepForward = true,
}) => {
  return (
    <div
      data-testid="causality-header"
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
      {/* Subtle temporal border indicator */}
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
              Causal Investigation Intelligence
            </h1>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>

          <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
            Deterministic cause-and-effect synthesis. Active Mode:{' '}
            <strong style={{ color: 'var(--tsi-text-primary)' }}>{activeMode}</strong>
            {targetTitle && (
              <span>
                {' '}
                • Investigating: <strong style={{ color: 'var(--tsi-accent-primary)' }}>{targetTitle}</strong>
              </span>
            )}
          </p>
        </div>

        {/* Temporal Stepper Controls */}
        <div
          role="group"
          aria-label="Causality Horizon Controls"
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

      {/* Metrics Badges */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <Badge variant="neutral" data-testid="causal-nodes-count-badge">
          {nodeCount} {nodeCount === 1 ? 'Causal Node' : 'Causal Nodes'}
        </Badge>
        <Badge variant="neutral" data-testid="causal-relations-count-badge">
          {edgeCount} {edgeCount === 1 ? 'Causal Relation' : 'Causal Relations'}
        </Badge>
      </div>
    </div>
  );
};
