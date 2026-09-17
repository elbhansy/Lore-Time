import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { EmptyState } from '../../../components/feedback/EmptyState';
import {
  NarrativeCausalPathDTO,
  NarrativeCausalStepDTO,
  TemporalNarrativeCausalExplanationDTO,
} from '../../../api/contracts/read-models';

export interface CharacterCausalitySectionProps {
  synthesis: TemporalNarrativeCausalExplanationDTO | null | undefined;
  readerChapter: number;
  onInspectStep: (step: NarrativeCausalStepDTO) => void;
}

export const CharacterCausalitySection: React.FC<CharacterCausalitySectionProps> = ({
  synthesis,
  readerChapter,
  onInspectStep,
}) => {
  const narrativePaths = synthesis?.narrative_paths || [];
  const narrativeSteps = synthesis?.narrative_steps || [];

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Causal History & Impact Propagation
          </h2>
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            Known Through Ch. {readerChapter}
          </Badge>
        </div>
        <p style={{ margin: '4px 0 0', fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          Deterministic causal chains linking upstream triggers to character state changes and downstream consequences.
        </p>
      </div>

      {narrativePaths.length === 0 && narrativeSteps.length === 0 ? (
        <EmptyState
          title="No Causal Chains Synthesized"
          description="No upstream causal chains directly targeting this character have been derived for this chapter horizon."
        />
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Causal Paths */}
          {narrativePaths.map((path: NarrativeCausalPathDTO) => (
            <div
              key={path.path_id}
              style={{
                padding: '12px 16px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                border: '1px solid var(--tsi-border-subtle)',
                borderRadius: 'var(--tsi-radius-md)',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Badge variant="default" style={{ fontSize: '0.6875rem' }}>
                    Ch. {path.start_chapter} → Ch. {path.end_chapter}
                  </Badge>
                  <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
                    Depth: {path.depth}
                  </Badge>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                    Cumulative Impact: {path.cumulative_impact_score.toFixed(2)}
                  </span>
                </div>
              </div>

              {/* Steps along the causal path */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', paddingLeft: '8px' }}>
                {path.steps.map((step, idx) => (
                  <div
                    key={step.step_id}
                    onClick={() => onInspectStep(step)}
                    role="button"
                    tabIndex={0}
                    aria-label={`Causal step: ${step.state_change_summary || step.relation_type}`}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        onInspectStep(step);
                      }
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '10px',
                      padding: '6px 10px',
                      backgroundColor: 'var(--tsi-surface-primary)',
                      border: '1px solid var(--tsi-border-subtle)',
                      borderRadius: 'var(--tsi-radius-sm)',
                      cursor: 'pointer',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                      <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                        #{idx + 1} Ch. {step.chapter}
                      </span>
                      <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-primary)' }}>
                        {step.state_change_summary || `${step.relation_type} on entities`}
                      </span>
                      <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>
                        {step.relation_type}
                      </Badge>
                    </div>
                    <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-accent-primary)' }}>
                      Details 🔍
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
