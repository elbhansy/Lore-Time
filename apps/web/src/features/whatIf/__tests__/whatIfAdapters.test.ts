import { describe, it, expect } from 'vitest';
import {
  adaptHypotheticalImpacts,
  buildCounterfactualScenario,
} from '../whatIfAdapters';
import {
  TemporalComparisonResponse,
  CounterfactualAssumption,
} from '../../../api/contracts/read-models';

describe('whatIfAdapters', () => {
  const mockComparison: TemporalComparisonResponse = {
    from_chapter: 5,
    to_chapter: 10,
    summary: {
      characters_introduced: 1,
      characters_removed: 1,
      power_changes: 1,
      skills_unlocked: 2,
      relationships_changed: 1,
    },
    character_changes: [
      {
        character_id: 'char-lyra',
        change_type: 'REMOVED',
        before_status: 'alive',
        after_status: 'dead',
      },
    ],
    power_changes: [
      {
        character_id: 'char-kael',
        before_rank: 'Adept',
        after_rank: 'Master',
      },
    ],
    relationship_changes: [
      {
        source_id: 'char-lyra',
        target_id: 'char-kael',
        change_type: 'CHANGED',
        before_type: 'ALLY',
        after_type: 'ENEMY',
      },
    ],
    skill_changes: [
      {
        character_id: 'char-kael',
        unlocked_skills: ['Solar Flare', 'Chrono Aegis'],
      },
    ],
  };

  const mockAssumption: CounterfactualAssumption = {
    target_chapter: 6,
    assumption_type: 'ALTER_OUTCOME',
    target_entity_id: 'char-lyra',
    target_entity_name: 'Lyra Valen',
    proposed_value: 'Survives the ambush',
    justification: 'What if Lyra activated her chronolith shield in time?',
  };

  describe('buildCounterfactualScenario', () => {
    it('stamps is_hypothetical: true unconditionally', () => {
      const scenario = buildCounterfactualScenario('series-1', 10, mockAssumption, mockComparison);
      expect(scenario.is_hypothetical).toBe(true);
      expect(scenario.reader_chapter).toBe(10);
      expect(scenario.base_chapter).toBe(6);
    });
  });

  describe('adaptHypotheticalImpacts', () => {
    it('maps comparison changes into formatted impact rows carrying isHypothetical: true', () => {
      const scenario = buildCounterfactualScenario('series-1', 10, mockAssumption, mockComparison);
      const impacts = adaptHypotheticalImpacts(mockComparison, scenario);

      expect(impacts).toHaveLength(4);
      expect(impacts.every((i) => i.isHypothetical === true)).toBe(true);

      const charImpact = impacts.find((i) => i.entityType === 'CHARACTER');
      expect(charImpact).toBeDefined();
      expect(charImpact?.entityName).toBe('char-lyra');
      expect(charImpact?.canonicalValue).toBe('alive');
      expect(charImpact?.hypotheticalValue).toBe('dead');

      const relImpact = impacts.find((i) => i.entityType === 'RELATIONSHIP');
      expect(relImpact).toBeDefined();
      expect(relImpact?.canonicalValue).toBe('ALLY');
      expect(relImpact?.hypotheticalValue).toBe('ENEMY');
    });

    it('returns fallback row when comparison has 0 changes but scenario is present', () => {
      const emptyComparison: TemporalComparisonResponse = {
        from_chapter: 1,
        to_chapter: 10,
        summary: {},
        character_changes: [],
        power_changes: [],
        relationship_changes: [],
        skill_changes: [],
      };
      const scenario = buildCounterfactualScenario('series-1', 10, mockAssumption, emptyComparison);
      const impacts = adaptHypotheticalImpacts(emptyComparison, scenario);

      expect(impacts).toHaveLength(1);
      expect(impacts[0].entityName).toBe('Lyra Valen');
      expect(impacts[0].hypotheticalValue).toBe('Survives the ambush');
      expect(impacts[0].isHypothetical).toBe(true);
    });
  });
});
