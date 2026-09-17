import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';
import { Skeleton } from '../../../components/feedback/Skeleton';
import { CharacterArcTrajectory } from './CharacterArcTrajectory';
import {
  FormattedCharacterArc,
  FormattedArcMilestone,
  FormattedTurningPoint,
  FormattedNarrativePhase,
} from '../narrativeAdapters';

export interface DiscoveryCharacterItem {
  id: string;
  name: string;
  activePhaseTitle?: string | null;
}

export interface CharacterArcExplorerProps {
  characters: DiscoveryCharacterItem[];
  selectedCharacterId: string | null;
  onSelectCharacter: (characterId: string) => void;
  arcData: FormattedCharacterArc | null;
  isLoadingArc: boolean;
  readerChapter: number;
  onInspectMilestone: (m: FormattedArcMilestone) => void;
  onInspectTurningPoint: (tp: FormattedTurningPoint) => void;
  onInspectPhase: (phase: FormattedNarrativePhase) => void;
}

export const CharacterArcExplorer: React.FC<CharacterArcExplorerProps> = ({
  characters,
  selectedCharacterId,
  onSelectCharacter,
  arcData,
  isLoadingArc,
  readerChapter,
  onInspectMilestone,
  onInspectTurningPoint,
  onInspectPhase,
}) => {
  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
              Character Arc Explorer
            </h2>
            <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
              Known Through Ch. {readerChapter}
            </Badge>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Select a visible character to inspect their canonical evolutionary arc on-demand.
          </span>
        </div>
      </div>

      {/* Character Selector Pills */}
      <div>
        <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
          Visible Characters ({characters.length})
        </span>
        <div
          data-testid="character-selector-list"
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: '8px',
            marginTop: '8px',
            maxHeight: '120px',
            overflowY: 'auto',
          }}
        >
          {characters.length === 0 ? (
            <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
              No characters have been introduced by Chapter {readerChapter}.
            </span>
          ) : (
            characters.map((char) => {
              const isSelected = selectedCharacterId === char.id;
              return (
                <button
                  key={char.id}
                  onClick={() => onSelectCharacter(char.id)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 'var(--tsi-radius-full)',
                    border: isSelected
                      ? '1px solid var(--tsi-accent-primary)'
                      : '1px solid var(--tsi-border-subtle)',
                    backgroundColor: isSelected
                      ? 'rgba(99, 102, 241, 0.2)'
                      : 'var(--tsi-surface-secondary)',
                    color: isSelected ? 'var(--tsi-text-primary)' : 'var(--tsi-text-secondary)',
                    fontSize: '0.8125rem',
                    fontWeight: isSelected ? 600 : 400,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <span>{char.name}</span>
                  {char.activePhaseTitle && (
                    <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)' }}>
                      • {char.activePhaseTitle}
                    </span>
                  )}
                </button>
              );
            })
          )}
        </div>
      </div>

      {/* Selected Character Arc Content */}
      <div style={{ marginTop: '8px', borderTop: '1px solid var(--tsi-border-subtle)', paddingTop: '16px' }}>
        {!selectedCharacterId ? (
          <EmptyState
            title="No Character Selected"
            description="Select a character from the roster above to query their canonical narrative arc and trajectory."
          />
        ) : isLoadingArc ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <Skeleton height={90} borderRadius="var(--tsi-radius-md)" />
            <Skeleton height={140} borderRadius="var(--tsi-radius-md)" />
          </div>
        ) : !arcData ? (
          <EmptyState
            title="No Arc Data Available"
            description="Unable to load narrative arc for the selected character."
          />
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Trajectory Summary */}
            <CharacterArcTrajectory trajectory={arcData.trajectory} readerChapter={readerChapter} />

            {/* Character Narrative Phases */}
            {arcData.phases.length > 0 && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Character Phases ({arcData.phases.length})
                </span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '6px' }}>
                  {arcData.phases.map((p) => (
                    <div
                      key={p.id}
                      style={{
                        padding: '8px 12px',
                        backgroundColor: p.isActiveAtHorizon ? 'var(--tsi-surface-elevated)' : 'var(--tsi-surface-secondary)',
                        border: p.isActiveAtHorizon ? '1px solid var(--tsi-accent-primary)' : '1px solid var(--tsi-border-subtle)',
                        borderRadius: 'var(--tsi-radius-md)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '8px',
                      }}
                    >
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '0.8125rem', color: 'var(--tsi-text-primary)' }}>
                          Phase {p.phaseNumber}: {p.title}
                        </div>
                        <div style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-secondary)' }}>
                          Ch. {p.fromChapter} – {p.toChapter}
                        </div>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => onInspectPhase(p)}>
                        ↗
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Character Arc Milestones */}
            <div>
              <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                Character Milestones ({arcData.milestones.length})
              </span>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px',
                  marginTop: '6px',
                  maxHeight: '220px',
                  overflowY: 'auto',
                }}
              >
                {arcData.milestones.length === 0 ? (
                  <span style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-muted)' }}>
                    No milestones recorded for this character prior to Chapter {readerChapter}.
                  </span>
                ) : (
                  arcData.milestones.map((m) => (
                    <div
                      key={m.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        backgroundColor: 'var(--tsi-surface-secondary)',
                        borderRadius: 'var(--tsi-radius-sm)',
                        border: '1px solid var(--tsi-border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
                          Ch. {m.chapter}
                        </Badge>
                        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: 'var(--tsi-text-primary)' }}>
                          {m.milestoneType.replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
                          • {m.description}
                        </span>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => onInspectMilestone(m)}>
                        Inspect ↗
                      </Button>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Character Turning Points */}
            {arcData.turningPoints.length > 0 && (
              <div>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Character Turning Points ({arcData.turningPoints.length})
                </span>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: '6px' }}>
                  {arcData.turningPoints.map((tp) => (
                    <div
                      key={tp.id}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '8px 12px',
                        backgroundColor: 'var(--tsi-surface-secondary)',
                        borderRadius: 'var(--tsi-radius-sm)',
                        border: '1px solid var(--tsi-border-subtle)',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Badge variant="warning" style={{ fontSize: '0.6875rem' }}>
                          Ch. {tp.chapter}
                        </Badge>
                        <span style={{ fontSize: '0.8125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
                          {tp.turningPointType.replace(/_/g, ' ')}
                        </span>
                        <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-secondary)' }}>
                          • {tp.description}
                        </span>
                      </div>
                      <Button size="sm" variant="ghost" onClick={() => onInspectTurningPoint(tp)}>
                        Inspect ↗
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
};
