import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import { EmptyState } from '../../../components/feedback/EmptyState';

export interface CharacterRosterProps {
  seriesId: string;
  readerChapter: number;
  activePhasesByCharacter: Record<string, string>;
  totalCharacters: number;
}

export const CharacterRoster: React.FC<CharacterRosterProps> = ({
  seriesId,
  readerChapter,
  activePhasesByCharacter,
  totalCharacters,
}) => {
  const navigate = useNavigate();
  const characterEntries = Object.entries(activePhasesByCharacter);

  return (
    <Card style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.125rem', fontWeight: 600, color: 'var(--tsi-text-primary)' }}>
            Active Character Trajectories
          </h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Narrative phases and states attained as of Chapter {readerChapter}
          </span>
        </div>

        <Button
          size="sm"
          variant="ghost"
          onClick={() => navigate(`/series/${seriesId}/characters`)}
          title="Open complete character explorer"
        >
          View All Characters ({totalCharacters}) →
        </Button>
      </div>

      {characterEntries.length === 0 ? (
        <EmptyState
          title="No Active Characters"
          description={`No character arcs have commenced or attained named narrative phases by Chapter ${readerChapter}.`}
        />
      ) : (
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
            gap: '10px',
          }}
        >
          {characterEntries.map(([charId, phaseTitle]) => (
            <div
              key={charId}
              onClick={() => navigate(`/series/${seriesId}/characters/${encodeURIComponent(charId)}`)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  navigate(`/series/${seriesId}/characters/${encodeURIComponent(charId)}`);
                }
              }}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '6px',
                padding: '12px 14px',
                backgroundColor: 'var(--tsi-surface-secondary)',
                borderRadius: 'var(--tsi-radius-md)',
                border: '1px solid var(--tsi-border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--tsi-text-primary)' }}>
                  {charId}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--tsi-accent-primary)' }}>Profile ↗</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ fontSize: '0.6875rem', color: 'var(--tsi-text-muted)', textTransform: 'uppercase' }}>
                  Current Phase:
                </span>
                <Badge variant="default" style={{ fontSize: '0.6875rem' }}>
                  {phaseTitle}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};
