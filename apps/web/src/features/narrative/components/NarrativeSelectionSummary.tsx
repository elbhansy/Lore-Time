import React from 'react';
import { Card } from '../../../components/ui/Card';
import { Badge } from '../../../components/ui/Badge';
import { Button } from '../../../components/ui/Button';
import {
  FormattedNarrativePhase,
  FormattedArcMilestone,
  FormattedTurningPoint,
  FormattedCharacterArc,
} from '../narrativeAdapters';

export type SelectedNarrativeEntity =
  | { type: 'PHASE'; data: FormattedNarrativePhase }
  | { type: 'MILESTONE'; data: FormattedArcMilestone }
  | { type: 'TURNING_POINT'; data: FormattedTurningPoint }
  | { type: 'CHARACTER'; data: FormattedCharacterArc; name: string };

export interface NarrativeSelectionSummaryProps {
  selection: SelectedNarrativeEntity | null;
  seriesId: string;
  readerChapter: number;
  onOpenInspector: () => void;
  onNavigateToCharacter?: (characterId: string) => void;
  onNavigateToTimeline?: () => void;
  onClearSelection: () => void;
}

export const NarrativeSelectionSummary: React.FC<NarrativeSelectionSummaryProps> = ({
  selection,
  seriesId: _seriesId,
  readerChapter,
  onOpenInspector,
  onNavigateToCharacter,
  onNavigateToTimeline,
  onClearSelection,
}) => {
  if (!selection) {
    return (
      <Card
        style={{
          padding: '14px 18px',
          backgroundColor: 'var(--tsi-surface-primary)',
          border: '1px solid var(--tsi-border-subtle)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.8125rem',
          color: 'var(--tsi-text-muted)',
        }}
      >
        <span>Select any phase, milestone, turning point, or character to inspect context.</span>
        <Badge variant="neutral" style={{ fontSize: '0.6875rem' }}>
          Horizon: Ch. {readerChapter}
        </Badge>
      </Card>
    );
  }

  const renderContent = () => {
    switch (selection.type) {
      case 'PHASE': {
        const p = selection.data;
        return {
          badge: 'PHASE',
          title: `Phase ${p.phaseNumber}: ${p.title}`,
          subtitle: `Chapters ${p.fromChapter} – ${p.toChapter} • ${p.milestoneCount} Milestones`,
          characterId: p.characterId,
        };
      }
      case 'MILESTONE': {
        const m = selection.data;
        return {
          badge: 'MILESTONE',
          title: `${m.milestoneType.replace(/_/g, ' ')} (Ch. ${m.chapter})`,
          subtitle: m.description,
          characterId: m.characterId,
        };
      }
      case 'TURNING_POINT': {
        const tp = selection.data;
        return {
          badge: `TURNING POINT • ${tp.significance.toUpperCase()}`,
          title: `${tp.turningPointType.replace(/_/g, ' ')} (Ch. ${tp.chapter})`,
          subtitle: tp.description,
          characterId: tp.characterId,
        };
      }
      case 'CHARACTER': {
        const c = selection.data;
        return {
          badge: 'CHARACTER ARC',
          title: `${selection.name} — Evolutionary Arc`,
          subtitle: `Known through Ch. ${c.readerChapter} • ${c.milestones.length} milestones • ${c.turningPoints.length} turning points`,
          characterId: c.characterId,
        };
      }
    }
  };

  const { badge, title, subtitle, characterId } = renderContent();

  return (
    <Card
      data-testid="narrative-selection-summary"
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '16px',
        padding: '16px 20px',
        backgroundColor: 'var(--tsi-surface-elevated)',
        border: '1px solid var(--tsi-accent-primary)',
        borderRadius: 'var(--tsi-radius-lg)',
      }}
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxWidth: '65%' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Badge variant="temporal" style={{ fontSize: '0.6875rem' }}>
            {badge}
          </Badge>
          <span style={{ fontSize: '0.75rem', color: 'var(--tsi-text-muted)' }}>
            Authoritative Horizon: Ch. {readerChapter}
          </span>
        </div>
        <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--tsi-text-primary)' }}>
          {title}
        </div>
        <div style={{ fontSize: '0.8125rem', color: 'var(--tsi-text-secondary)' }}>
          {subtitle}
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '8px' }}>
        <Button size="sm" variant="primary" onClick={onOpenInspector} title="Open detailed provenance & state inspector">
          Deep Inspector ↗
        </Button>
        {characterId && onNavigateToCharacter && (
          <Button
            size="sm"
            variant="secondary"
            onClick={() => onNavigateToCharacter(characterId)}
            title="Inspect character profile"
          >
            Character Profile ↗
          </Button>
        )}
        {onNavigateToTimeline && (
          <Button
            size="sm"
            variant="secondary"
            onClick={onNavigateToTimeline}
            title="Open chronological timeline"
          >
            Timeline Feed ↗
          </Button>
        )}
        <Button size="sm" variant="ghost" onClick={onClearSelection} title="Deselect item">
          ✕
        </Button>
      </div>
    </Card>
  );
};
