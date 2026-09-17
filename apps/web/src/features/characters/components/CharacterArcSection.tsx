import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { ArcMilestoneDTO, NarrativePhaseDTO } from '../../../api/contracts/read-models';

export interface CharacterArcSectionProps {
  phases: NarrativePhaseDTO[];
  milestones: ArcMilestoneDTO[];
  readerChapter: number;
  onInspectMilestone: (milestone: ArcMilestoneDTO) => void;
}

export const CharacterArcSection: React.FC<CharacterArcSectionProps> = ({
  phases,
  milestones,
  readerChapter,
  onInspectMilestone,
}) => {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Character Arc & Narrative Phases
          </h2>
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            Known Through Ch. {readerChapter}
          </Badge>
        </div>
        <p style={{ margin: '4px 0 0', fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          Chronological arc milestones and phased evolution derived from canonical narrative transitions.
        </p>
      </div>

      {/* Narrative Phases Track */}
      <div>
        <h3 style={{ margin: '0 0 10px', fontSize: '0.875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Narrative Phases Progression
        </h3>
        {phases.length === 0 ? (
          <EmptyState
            title="No Phases Discovered"
            description="No distinct narrative phases have been attained within the visible story horizon."
          />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px' }}>
            {phases.map((phase) => (
              <div
                key={phase.phase_id}
                style={{
                  padding: '12px 14px',
                  backgroundColor: phase.is_active_at_horizon ? 'var(--tsi-surface-elevated)' : 'var(--tsi-surface-secondary)',
                  border: phase.is_active_at_horizon
                    ? '1px solid var(--tsi-accent-primary)'
                    : '1px solid var(--tsi-border-subtle)',
                  borderRadius: 'var(--tsi-radius-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                    Phase {phase.phase_number}
                  </span>
                  {phase.is_active_at_horizon && (
                    <Badge variant="temporal" style={{ fontSize: '0.625rem' }}>
                      CURRENT
                    </Badge>
                  )}
                </div>
                <span style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--tsi-text-primary)' }}>
                  {phase.title}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-secondary)' }}>
                  Chapters {phase.from_chapter} – {phase.to_chapter}
                </span>
                {phase.dominant_faction && (
                  <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)' }}>
                    Faction: {phase.dominant_faction}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Arc Milestones Sequence */}
      <div>
        <h3 style={{ margin: '0 0 10px', fontSize: '0.875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          Milestone Sequence ({milestones.length})
        </h3>
        {milestones.length === 0 ? (
          <EmptyState
            title="No Milestones Reached"
            description="This character has not triggered canonical arc milestones prior to the current chapter."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {milestones.map((m) => (
              <div
                key={m.milestone_id}
                onClick={() => onInspectMilestone(m)}
                role="button"
                tabIndex={0}
                aria-label={`Milestone: ${m.description}, Chapter ${m.chapter}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    onInspectMilestone(m);
                  }
                }}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '12px',
                  padding: '10px 14px',
                  backgroundColor: 'var(--tsi-surface-secondary)',
                  border: '1px solid var(--tsi-border-subtle)',
                  borderRadius: 'var(--tsi-radius-md)',
                  cursor: 'pointer',
                  transition: 'background-color 0.12s ease',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
                  <Badge variant="default" style={{ fontSize: '0.6875rem' }}>
                    Ch. {m.chapter}
                  </Badge>
                  <span style={{ fontWeight: 500, fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                    {m.description}
                  </span>
                  <Badge variant="neutral" style={{ fontSize: '0.625rem' }}>
                    {m.milestone_type}
                  </Badge>
                </div>
                <span style={{ fontSize: '0.75rem', color: 'var(--tsi-accent-primary)', flexShrink: 0 }}>
                  Inspect 🔍
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};
