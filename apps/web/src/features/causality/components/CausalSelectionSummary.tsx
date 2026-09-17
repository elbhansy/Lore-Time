import React from 'react';
import { Link } from 'react-router-dom';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { TemporalNarrativeCausalExplanationDTO, NarrativeCausalStepDTO } from '../../../api/contracts/read-models';

export interface CausalSelectionSummaryProps {
  seriesId: string;
  readerChapter: number;
  mode: 'EVENT' | 'CHARACTER';
  targetId: string | null;
  targetTitle?: string | null;
  synthesis: TemporalNarrativeCausalExplanationDTO | null | undefined;
  selectedStep: NarrativeCausalStepDTO | null;
  onOpenInspector: () => void;
  onClearTarget: () => void;
}

/**
 * Compact workspace selection summary (RULE_05: surface decoupling).
 * Hosts minimal target metadata and metrics.
 * Full detailed synthesis, conflicts, and state JSON are housed exclusively in the Inspector Panel.
 */
export const CausalSelectionSummary: React.FC<CausalSelectionSummaryProps> = ({
  seriesId,
  readerChapter,
  mode,
  targetId,
  targetTitle,
  synthesis,
  selectedStep,
  onOpenInspector,
  onClearTarget,
}) => {
  if (!targetId) {
    return (
      <div
        data-testid="causal-selection-empty"
        style={{
          padding: '16px',
          backgroundColor: 'var(--tsi-surface-primary)',
          border: '1px dashed var(--tsi-border-subtle)',
          borderRadius: 'var(--tsi-radius-md)',
          color: 'var(--tsi-text-muted)',
          fontSize: '0.8125rem',
          textAlign: 'center',
        }}
      >
        Select an event or character target to inspect deterministic causal chains.
      </div>
    );
  }

  const stepsCount = synthesis?.narrative_steps?.length || 0;
  const pathsCount = synthesis?.narrative_paths?.length || 0;
  const conflictsCount = synthesis?.conflicts?.length || 0;

  return (
    <div
      data-testid="causal-selection-summary"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        padding: '16px',
        backgroundColor: 'var(--tsi-surface-primary)',
        border: '1px solid var(--tsi-border-subtle)',
        borderRadius: 'var(--tsi-radius-md)',
        boxShadow: '0 4px 16px rgba(0, 0, 0, 0.25)',
      }}
    >
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '8px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
            <h3
              data-testid="selected-causal-target-title"
              style={{
                margin: 0,
                fontSize: '1.0625rem',
                fontWeight: 600,
                color: 'var(--tsi-text-primary)',
              }}
            >
              {targetTitle || targetId}
            </h3>
            <Badge variant="temporal">{mode}</Badge>
          </div>
          <div
            style={{
              fontSize: '0.6875rem',
              color: 'var(--tsi-text-muted)',
              fontFamily: 'var(--tsi-font-mono)',
              marginTop: '2px',
            }}
          >
            ID: {targetId}
          </div>
        </div>

        <button
          type="button"
          onClick={onClearTarget}
          aria-label="Clear target selection"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--tsi-text-muted)',
            cursor: 'pointer',
            fontSize: '1.25rem',
            lineHeight: 1,
            padding: '2px 6px',
            borderRadius: 'var(--tsi-radius-sm)',
          }}
        >
          ×
        </button>
      </div>

      {/* Synthesis Headline if present */}
      {synthesis?.headline && (
        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)', fontStyle: 'italic' }}>
          "{synthesis.headline}"
        </p>
      )}

      {/* Metrics breakdown */}
      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
        <Badge variant="neutral">Paths: {pathsCount}</Badge>
        <Badge variant="neutral">Steps: {stepsCount}</Badge>
        {conflictsCount > 0 && <Badge variant="warning">Conflicts: {conflictsCount}</Badge>}
      </div>

      {/* Selected Step highlight if active */}
      {selectedStep && (
        <div
          style={{
            padding: '8px 10px',
            backgroundColor: 'var(--tsi-surface-secondary)',
            border: '1px solid var(--tsi-accent-primary)',
            borderRadius: 'var(--tsi-radius-sm)',
            fontSize: '0.75rem',
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 600, color: 'var(--tsi-text-primary)' }}>{selectedStep.relation_type}</span>
            <span style={{ color: 'var(--tsi-text-muted)' }}>Ch. {selectedStep.chapter}</span>
          </div>
          <div style={{ color: 'var(--tsi-text-secondary)' }}>{selectedStep.state_change_summary}</div>
        </div>
      )}

      {/* Actions: Open Inspector & Deep Navigation */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '4px' }}>
        <Button
          size="sm"
          variant="secondary"
          onClick={onOpenInspector}
          aria-label="Open detailed causal inspector"
          data-testid="inspect-causal-target-btn"
          style={{ width: '100%' }}
        >
          Open Deep Inspector ↗
        </Button>

        {mode === 'CHARACTER' ? (
          <Link
            to={`/series/${seriesId}/characters/${targetId}?chapter=${readerChapter}`}
            style={{ textDecoration: 'none' }}
          >
            <Button size="sm" variant="primary" style={{ width: '100%' }} data-testid="view-character-profile-link">
              View Character Arc Profile →
            </Button>
          </Link>
        ) : (
          <Link
            to={`/series/${seriesId}/timeline?chapter=${readerChapter}`}
            style={{ textDecoration: 'none' }}
          >
            <Button size="sm" variant="primary" style={{ width: '100%' }} data-testid="view-timeline-feed-link">
              View in Timeline Feed →
            </Button>
          </Link>
        )}
      </div>
    </div>
  );
};
