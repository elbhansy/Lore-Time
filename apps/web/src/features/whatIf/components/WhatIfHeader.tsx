import React from 'react';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';

export interface WhatIfHeaderProps {
  seriesId: string;
  readerChapter: number;
  totalChapters?: number;
  isSimulating: boolean;
  onJumpToStart?: () => void;
  onStepBackward?: () => void;
  onStepForward?: () => void;
  onJumpToHorizon?: () => void;
  canStepBackward?: boolean;
  canStepForward?: boolean;
}

export const WhatIfHeader: React.FC<WhatIfHeaderProps> = ({
  seriesId: _seriesId,
  readerChapter,
  totalChapters = 200,
  isSimulating,
  onJumpToStart,
  onStepBackward,
  onStepForward,
  onJumpToHorizon,
  canStepBackward = true,
  canStepForward = true,
}) => {
  return (
    <div
      data-testid="what-if-header"
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
      {/* Visual warning/indicator: Amber/Violet for counterfactual mode */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          bottom: 0,
          width: '3px',
          backgroundColor: isSimulating ? 'var(--tsi-status-warning)' : 'var(--tsi-accent-primary)',
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
              Counterfactual / What-If Intelligence Experience
            </h1>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
            {isSimulating && (
              <Badge variant="warning" style={{ fontSize: '0.6875rem' }}>
                HYPOTHETICAL SIMULATION
              </Badge>
            )}
          </div>

          <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
            Simulate alternative narrative choices without modifying canonical world state. All outcomes are explicitly marked as hypothetical.
          </p>
        </div>

        {/* Status indicator badges */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px 12px',
              backgroundColor: 'var(--tsi-surface-secondary)',
              borderRadius: 'var(--tsi-radius-md)',
              border: '1px solid var(--tsi-border-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Persistence:
            </span>
            <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--tsi-status-success)' }}>
              Read-Only (No DB Write)
            </span>
          </div>

          <div
            style={{
              padding: '6px 12px',
              backgroundColor: 'var(--tsi-surface-secondary)',
              borderRadius: 'var(--tsi-radius-md)',
              border: '1px solid var(--tsi-border-subtle)',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
            }}
          >
            <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
              Safety:
            </span>
            <span style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--tsi-status-warning)' }}>
              Isolated Sandbox
            </span>
          </div>
        </div>
      </div>

      {/* Temporal Navigation Controls */}
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px',
          paddingTop: '8px',
          borderTop: '1px solid var(--tsi-border-subtle)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Horizon Control:
          </span>
          <Button
            size="sm"
            variant="secondary"
            onClick={onJumpToStart}
            disabled={!canStepBackward || readerChapter <= 1}
            title="Jump to Chapter 1"
          >
            ⇤ Ch. 1
          </Button>
          <Button
            data-testid="temporal-step-back-btn"
            size="sm"
            variant="secondary"
            onClick={onStepBackward}
            disabled={!canStepBackward}
            title="Step backward one chapter"
          >
            ← Prev Ch.
          </Button>
          <span
            style={{
              padding: '4px 10px',
              fontSize: '0.8125rem',
              fontWeight: 600,
              fontFamily: 'var(--tsi-font-mono)',
              color: 'var(--tsi-text-primary)',
              backgroundColor: 'var(--tsi-surface-elevated)',
              borderRadius: 'var(--tsi-radius-md)',
              border: '1px solid var(--tsi-border-default)',
            }}
          >
            Chapter {readerChapter} / {totalChapters}
          </span>
          <Button
            data-testid="temporal-step-forward-btn"
            size="sm"
            variant="secondary"
            onClick={onStepForward}
            disabled={!canStepForward || readerChapter >= totalChapters}
            title="Step forward one chapter"
          >
            Next Ch. →
          </Button>
          <Button
            size="sm"
            variant="secondary"
            onClick={onJumpToHorizon}
            disabled={!canStepForward || readerChapter >= totalChapters}
            title={`Jump to Horizon (Ch. ${totalChapters})`}
          >
            Ch. {totalChapters} ⇥
          </Button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
            Canonical Horizon Locked
          </Badge>
          <Badge variant="warning" style={{ fontSize: '0.6875rem' }}>
            NOT CANON
          </Badge>
        </div>
      </div>
    </div>
  );
};
