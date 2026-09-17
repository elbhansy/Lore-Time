import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { TemporalNarrativeCausalExplanationDTO } from '../../../api/contracts/read-models';

export interface CharacterSynthesisSectionProps {
  synthesis: TemporalNarrativeCausalExplanationDTO | null | undefined;
  readerChapter: number;
}

export const CharacterSynthesisSection: React.FC<CharacterSynthesisSectionProps> = ({
  synthesis,
  readerChapter,
}) => {
  if (!synthesis || (!synthesis.headline && Object.keys(synthesis.summary || {}).length === 0)) {
    return null;
  }

  const conflicts = synthesis.conflicts || [];

  return (
    <Card
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: '14px',
        borderLeft: '3px solid var(--tsi-accent-primary)',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="temporal" style={{ textTransform: 'uppercase', letterSpacing: '0.06em', fontSize: '0.6875rem' }}>
            NARRATIVE SYNTHESIS
          </Badge>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Analytical Narrative Interpretation • Ch. {readerChapter} Horizon
          </span>
        </div>
      </div>

      {/* Synthesis Headline */}
      {synthesis.headline && (
        <h3
          style={{
            margin: 0,
            fontSize: '1.0625rem',
            fontWeight: 600,
            color: 'var(--tsi-text-primary)',
            lineHeight: 1.3,
          }}
        >
          {synthesis.headline}
        </h3>
      )}

      {/* Summary dictionary or impact breakdown */}
      {synthesis.impact_breakdown && Object.keys(synthesis.impact_breakdown).length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Synthesized Impact Distribution
          </span>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
            {Object.entries(synthesis.impact_breakdown).map(([dim, count]) => (
              <Badge key={dim} variant="neutral" style={{ fontSize: '0.75rem' }}>
                {dim}: {count}
              </Badge>
            ))}
          </div>
        </div>
      )}

      {/* Synthesis Conflicts */}
      {conflicts.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '4px' }}>
          <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
            Narrative Conflicts & Dual Evidence
          </span>
          {conflicts.map((c) => (
            <div
              key={c.conflict_id}
              style={{
                padding: '6px 10px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                borderRadius: 'var(--tsi-radius-sm)',
                fontSize: '0.8125rem',
                color: 'var(--tsi-text-secondary)',
              }}
            >
              <strong>{c.conflict_type}:</strong> {c.evidence_summary} ({c.resolution_status})
            </div>
          ))}
        </div>
      )}

      <div style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', fontStyle: 'italic' }}>
        * Note: Narrative Synthesis represents high-level structural synthesis over deterministic canonical facts.
      </div>
    </Card>
  );
};
