import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { FormattedNarrativePhase } from '../narrativeAdapters';

export interface NarrativePhaseTimelineProps {
  phases: FormattedNarrativePhase[];
  readerChapter: number;
  onSelectPhase?: (phase: FormattedNarrativePhase) => void;
  selectedPhaseId?: string | null;
}

export const NarrativePhaseTimeline: React.FC<NarrativePhaseTimelineProps> = ({
  phases,
  readerChapter,
  onSelectPhase,
  selectedPhaseId,
}) => {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Narrative Phases Progression
            </h2>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Contiguous temporal segments bounded by canonical turning points up to the reader horizon.
          </span>
        </div>
      </div>

      {phases.length === 0 ? (
        <EmptyState
          title="No Narrative Phases Discovered"
          description={`No character or story narrative phases have crystallized prior to Chapter ${readerChapter}.`}
        />
      ) : (
        <div
          data-testid="narrative-phases-track"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '12px',
          }}
        >
          {phases.map((phase) => {
            const isSelected = selectedPhaseId === phase.id;
            return (
              <div
                key={phase.id}
                role="button"
                tabIndex={0}
                onClick={() => onSelectPhase?.(phase)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onSelectPhase?.(phase);
                  }
                }}
                style={{
                  padding: '14px 16px',
                  backgroundColor: isSelected
                    ? 'var(--tsi-surface-elevated)'
                    : phase.isActiveAtHorizon
                    ? 'rgba(99, 102, 241, 0.08)'
                    : 'var(--tsi-surface-secondary)',
                  border: isSelected
                    ? '2px solid var(--tsi-accent-primary)'
                    : phase.isActiveAtHorizon
                    ? '1px solid var(--tsi-accent-primary)'
                    : '1px solid var(--tsi-border-subtle)',
                  borderRadius: 'var(--tsi-radius-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  cursor: onSelectPhase ? 'pointer' : 'default',
                  transition: 'all 0.15s ease',
                  outline: 'none',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                    Phase {phase.phaseNumber}
                  </span>
                  {phase.isActiveAtHorizon && (
                    <Badge variant="temporal" style={{ fontSize: '0.625rem' }}>
                      CURRENT HORIZON
                    </Badge>
                  )}
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                  <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--tsi-text-primary)' }}>
                    {phase.title}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-secondary)' }}>
                    Chapters {phase.fromChapter} – {phase.toChapter}
                  </span>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '4px' }}>
                  <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
                    {phase.milestoneCount} Milestones
                  </Badge>
                  {phase.dominantFaction && (
                    <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
                      Faction: {phase.dominantFaction}
                    </Badge>
                  )}
                  {phase.rankAtPhaseEnd && (
                    <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
                      Rank: {phase.rankAtPhaseEnd}
                    </Badge>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
};
