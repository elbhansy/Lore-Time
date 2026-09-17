import { describe, it, expect } from 'vitest';
import {
  adaptNarrativePhases,
  adaptArcMilestones,
  adaptTurningPoints,
  adaptCharacterArc,
  adaptNarrativeTimeline,
} from '../narrativeAdapters';
import {
  NarrativePhaseDTO,
  ArcMilestoneDTO,
  TurningPointDTO,
  CharacterArcResponse,
} from '../../../api/contracts/read-models';

describe('narrativeAdapters', () => {
  const mockPhases: NarrativePhaseDTO[] = [
    {
      phase_id: 'phase-2',
      character_id: 'char-1',
      phase_number: 2,
      title: 'Ascension of Sol',
      from_chapter: 10,
      to_chapter: 25,
      milestone_ids: ['m-2', 'm-3'],
      is_active_at_horizon: false,
    },
    {
      phase_id: 'phase-1',
      character_id: 'char-1',
      phase_number: 1,
      title: 'Humble Beginnings',
      from_chapter: 1,
      to_chapter: 9,
      milestone_ids: ['m-1'],
      is_active_at_horizon: false,
    },
    {
      phase_id: 'phase-3',
      character_id: 'char-1',
      phase_number: 3,
      title: 'Future Empire',
      from_chapter: 30,
      to_chapter: 50,
      milestone_ids: ['m-4'],
      is_active_at_horizon: false,
    },
  ];

  const mockMilestones: ArcMilestoneDTO[] = [
    {
      milestone_id: 'm-2',
      character_id: 'char-1',
      chapter: 12,
      sequence: 1,
      event_id: 'evt-12',
      milestone_type: 'RANK_CHANGE',
      description: 'Attains Gold Rank',
      previous_state: { rank: 'Silver' },
      new_state: { rank: 'Gold' },
      is_canonical: true,
    },
    {
      milestone_id: 'm-1',
      character_id: 'char-1',
      chapter: 3,
      sequence: 1,
      event_id: 'evt-3',
      milestone_type: 'FIRST_APPEARANCE',
      description: 'First spotted at the academy',
      previous_state: {},
      new_state: { status: 'alive' },
      is_canonical: true,
    },
    {
      milestone_id: 'm-future',
      character_id: 'char-1',
      chapter: 25,
      sequence: 1,
      event_id: 'evt-25',
      milestone_type: 'DEATH',
      description: 'Future death spoiler',
      previous_state: {},
      new_state: { status: 'dead' },
      is_canonical: true,
    },
  ];

  const mockTurningPoints: TurningPointDTO[] = [
    {
      turning_point_id: 'tp-1',
      character_id: 'char-1',
      chapter: 10,
      sequence: 2,
      event_id: 'evt-10',
      turning_point_type: 'POWER_BREAKTHROUGH',
      significance: 'CRITICAL',
      description: 'Unlocks domain awakening',
      affected_dimensions: ['power', 'rank'],
      previous_state: {},
      resulting_state: { power: 1000 },
      is_analytical: true,
    },
    {
      turning_point_id: 'tp-future',
      character_id: 'char-1',
      chapter: 35,
      sequence: 1,
      event_id: 'evt-35',
      turning_point_type: 'FACTION_REALIGNMENT',
      significance: 'HIGH',
      description: 'Future defection',
      affected_dimensions: ['faction'],
      previous_state: {},
      resulting_state: {},
      is_analytical: true,
    },
  ];

  describe('adaptNarrativePhases', () => {
    it('filters out future phases beyond readerChapter and clamps toChapter', () => {
      const adapted = adaptNarrativePhases(mockPhases, 15);
      expect(adapted).toHaveLength(2);
      expect(adapted.map((p) => p.id)).toEqual(['phase-1', 'phase-2']);
      expect(adapted[1].toChapter).toBe(15); // Clamped from 25 to 15
    });

    it('returns empty array when input is null or undefined', () => {
      expect(adaptNarrativePhases(null, 10)).toEqual([]);
      expect(adaptNarrativePhases(undefined, 10)).toEqual([]);
    });

    it('preserves deterministic ordering by phaseNumber and fromChapter', () => {
      const adapted = adaptNarrativePhases(mockPhases, 100);
      expect(adapted[0].phaseNumber).toBe(1);
      expect(adapted[1].phaseNumber).toBe(2);
      expect(adapted[2].phaseNumber).toBe(3);
    });
  });

  describe('adaptArcMilestones', () => {
    it('strictly filters out milestones occurring after readerChapter', () => {
      const adapted = adaptArcMilestones(mockMilestones, 15);
      expect(adapted).toHaveLength(2);
      expect(adapted.find((m) => m.id === 'm-future')).toBeUndefined();
    });

    it('orders milestones deterministically by chapter then sequence', () => {
      const adapted = adaptArcMilestones(mockMilestones, 15);
      expect(adapted[0].id).toBe('m-1'); // Ch. 3
      expect(adapted[1].id).toBe('m-2'); // Ch. 12
    });
  });

  describe('adaptTurningPoints', () => {
    it('strictly filters out turning points occurring after readerChapter', () => {
      const adapted = adaptTurningPoints(mockTurningPoints, 20);
      expect(adapted).toHaveLength(1);
      expect(adapted[0].id).toBe('tp-1');
      expect(adapted.find((tp) => tp.id === 'tp-future')).toBeUndefined();
    });
  });

  describe('adaptCharacterArc', () => {
    it('adapts full CharacterArc aggregate with temporal bounds', () => {
      const arcResponse: CharacterArcResponse = {
        series_id: 'series-1',
        character_id: 'char-1',
        reader_chapter: 15,
        start_chapter: 1,
        end_chapter: 25,
        milestones: mockMilestones,
        turning_points: mockTurningPoints,
        phases: mockPhases,
        trajectory: {
          total_milestones: 3,
          total_turning_points: 2,
          total_phases: 3,
          current_status: 'alive',
          current_rank: 'Gold',
          current_faction: null,
          total_skills_unlocked: 4,
          total_relationships: 2,
          highest_significance: 'CRITICAL',
        },
      };

      const adapted = adaptCharacterArc(arcResponse, 15);
      expect(adapted).not.toBeNull();
      expect(adapted?.readerChapter).toBe(15);
      expect(adapted?.endChapter).toBe(15);
      expect(adapted?.milestones).toHaveLength(2);
      expect(adapted?.turningPoints).toHaveLength(1);
      expect(adapted?.phases).toHaveLength(2);
      expect(adapted?.trajectory?.highest_significance).toBe('CRITICAL');
    });

    it('returns null when arcResponse is null or undefined', () => {
      expect(adaptCharacterArc(null, 10)).toBeNull();
      expect(adaptCharacterArc(undefined, 10)).toBeNull();
    });
  });

  describe('adaptNarrativeTimeline', () => {
    it('unifies milestones and turning points into chronologically sorted timeline items', () => {
      const timeline = adaptNarrativeTimeline(mockMilestones, mockTurningPoints, 15);
      expect(timeline).toHaveLength(3);
      expect(timeline[0].chapter).toBe(3);
      expect(timeline[0].itemType).toBe('MILESTONE');
      expect(timeline[1].chapter).toBe(10);
      expect(timeline[1].itemType).toBe('TURNING_POINT');
      expect(timeline[2].chapter).toBe(12);
      expect(timeline[2].itemType).toBe('MILESTONE');
    });
  });
});
