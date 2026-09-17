import {
  ArcMilestoneDTO,
  TurningPointDTO,
  NarrativePhaseDTO,
  CharacterArcResponse,
  ArcTrajectorySummaryDTO,
} from '../../api/contracts/read-models';

/**
 * Phase 6.8 Pure Narrative Adapters
 * 
 * Strict rules:
 * - Structural transformation only.
 * - No narrative inference or LLM calls.
 * - No new scoring or trajectory calculation in React.
 * - Respect readerChapter as authoritative temporal horizon.
 * - Preserve exact MilestoneType, TurningPointType, and SignificanceLevel enums from Phase 5.1.
 */

export interface FormattedNarrativePhase {
  id: string;
  characterId: string;
  phaseNumber: number;
  title: string;
  fromChapter: number;
  toChapter: number;
  milestoneIds: string[];
  milestoneCount: number;
  turningPointId: string | null;
  dominantFaction: string | null;
  rankAtPhaseEnd: string | null;
  isActiveAtHorizon: boolean;
}

export interface FormattedArcMilestone {
  id: string;
  characterId: string;
  chapter: number;
  sequence: number;
  eventId: string;
  milestoneType: string;
  description: string;
  previousState: Record<string, unknown>;
  newState: Record<string, unknown>;
  isCanonical: boolean;
}

export interface FormattedTurningPoint {
  id: string;
  characterId: string;
  chapter: number;
  sequence: number;
  eventId: string;
  turningPointType: string;
  significance: string;
  description: string;
  affectedDimensions: string[];
  previousState: Record<string, unknown>;
  resultingState: Record<string, unknown>;
  isAnalytical: boolean;
}

export interface FormattedCharacterArc {
  seriesId: string;
  characterId: string;
  readerChapter: number;
  startChapter: number | null;
  endChapter: number | null;
  milestones: FormattedArcMilestone[];
  turningPoints: FormattedTurningPoint[];
  phases: FormattedNarrativePhase[];
  trajectory: ArcTrajectorySummaryDTO | null;
}

export interface FormattedNarrativeTimelineItem {
  id: string;
  itemType: 'MILESTONE' | 'TURNING_POINT';
  chapter: number;
  sequence: number;
  characterId: string;
  eventId: string;
  typeBadge: string;
  significance?: string;
  title: string;
  description: string;
  metadata: Record<string, unknown>;
}

/**
 * Adapts narrative phases with temporal filtering and validation.
 */
export function adaptNarrativePhases(
  phases: NarrativePhaseDTO[] | undefined | null,
  readerChapter: number
): FormattedNarrativePhase[] {
  if (!phases || !Array.isArray(phases)) return [];

  return phases
    .filter((phase) => phase.from_chapter <= readerChapter)
    .map((phase) => ({
      id: phase.phase_id,
      characterId: phase.character_id,
      phaseNumber: phase.phase_number,
      title: phase.title,
      fromChapter: phase.from_chapter,
      toChapter: Math.min(phase.to_chapter, readerChapter),
      milestoneIds: Array.isArray(phase.milestone_ids) ? [...phase.milestone_ids] : [],
      milestoneCount: Array.isArray(phase.milestone_ids) ? phase.milestone_ids.length : 0,
      turningPointId: phase.turning_point_id || null,
      dominantFaction: phase.dominant_faction || null,
      rankAtPhaseEnd: phase.rank_at_phase_end || null,
      isActiveAtHorizon: phase.is_active_at_horizon,
    }))
    .sort((a, b) => a.phaseNumber - b.phaseNumber || a.fromChapter - b.fromChapter);
}

/**
 * Adapts canonical arc milestones with temporal filtering.
 */
export function adaptArcMilestones(
  milestones: ArcMilestoneDTO[] | undefined | null,
  readerChapter: number
): FormattedArcMilestone[] {
  if (!milestones || !Array.isArray(milestones)) return [];

  return milestones
    .filter((m) => m.chapter <= readerChapter)
    .map((m) => ({
      id: m.milestone_id,
      characterId: m.character_id,
      chapter: m.chapter,
      sequence: m.sequence,
      eventId: m.event_id,
      milestoneType: m.milestone_type,
      description: m.description,
      previousState: m.previous_state || {},
      newState: m.new_state || {},
      isCanonical: m.is_canonical,
    }))
    .sort((a, b) => a.chapter - b.chapter || a.sequence - b.sequence || a.id.localeCompare(b.id));
}

/**
 * Adapts turning points with temporal filtering.
 */
export function adaptTurningPoints(
  turningPoints: TurningPointDTO[] | undefined | null,
  readerChapter: number
): FormattedTurningPoint[] {
  if (!turningPoints || !Array.isArray(turningPoints)) return [];

  return turningPoints
    .filter((tp) => tp.chapter <= readerChapter)
    .map((tp) => ({
      id: tp.turning_point_id,
      characterId: tp.character_id,
      chapter: tp.chapter,
      sequence: tp.sequence,
      eventId: tp.event_id,
      turningPointType: tp.turning_point_type,
      significance: tp.significance,
      description: tp.description,
      affectedDimensions: Array.isArray(tp.affected_dimensions) ? [...tp.affected_dimensions] : [],
      previousState: tp.previous_state || {},
      resultingState: tp.resulting_state || {},
      isAnalytical: tp.is_analytical,
    }))
    .sort((a, b) => a.chapter - b.chapter || a.sequence - b.sequence || a.id.localeCompare(b.id));
}

/**
 * Adapts a character arc response aggregate.
 */
export function adaptCharacterArc(
  arcResponse: CharacterArcResponse | undefined | null,
  readerChapter: number
): FormattedCharacterArc | null {
  if (!arcResponse) return null;

  return {
    seriesId: arcResponse.series_id,
    characterId: arcResponse.character_id,
    readerChapter: Math.min(arcResponse.reader_chapter, readerChapter),
    startChapter: arcResponse.start_chapter ?? null,
    endChapter: arcResponse.end_chapter ? Math.min(arcResponse.end_chapter, readerChapter) : null,
    milestones: adaptArcMilestones(arcResponse.milestones, readerChapter),
    turningPoints: adaptTurningPoints(arcResponse.turning_points, readerChapter),
    phases: adaptNarrativePhases(arcResponse.phases, readerChapter),
    trajectory: arcResponse.trajectory || null,
  };
}

/**
 * Combines milestones and turning points into a chronologically unified narrative timeline feed.
 */
export function adaptNarrativeTimeline(
  milestones: ArcMilestoneDTO[] | undefined | null,
  turningPoints: TurningPointDTO[] | undefined | null,
  readerChapter: number
): FormattedNarrativeTimelineItem[] {
  const adaptedMilestones = adaptArcMilestones(milestones, readerChapter);
  const adaptedTurningPoints = adaptTurningPoints(turningPoints, readerChapter);

  const items: FormattedNarrativeTimelineItem[] = [
    ...adaptedMilestones.map((m) => ({
      id: m.id,
      itemType: 'MILESTONE' as const,
      chapter: m.chapter,
      sequence: m.sequence,
      characterId: m.characterId,
      eventId: m.eventId,
      typeBadge: m.milestoneType,
      title: `${m.milestoneType.replace(/_/g, ' ')}`,
      description: m.description,
      metadata: {
        isCanonical: m.isCanonical,
        previousState: m.previousState,
        newState: m.newState,
      },
    })),
    ...adaptedTurningPoints.map((tp) => ({
      id: tp.id,
      itemType: 'TURNING_POINT' as const,
      chapter: tp.chapter,
      sequence: tp.sequence,
      characterId: tp.characterId,
      eventId: tp.eventId,
      typeBadge: tp.turningPointType,
      significance: tp.significance,
      title: `${tp.turningPointType.replace(/_/g, ' ')}`,
      description: tp.description,
      metadata: {
        significance: tp.significance,
        affectedDimensions: tp.affectedDimensions,
        previousState: tp.previousState,
        resultingState: tp.resultingState,
      },
    })),
  ];

  return items.sort((a, b) => a.chapter - b.chapter || a.sequence - b.sequence || a.id.localeCompare(b.id));
}
