import {
  CounterfactualAssumption,
  CounterfactualScenarioDTO,
  TemporalComparisonResponse,
  CharacterDiffDTO,
  PowerDiffDTO,
  RelationshipDiffDTO,
  SkillDiffDTO,
} from '../../api/contracts/read-models';

/**
 * Phase 6.9 Pure Counterfactual / What-If Adapters
 * 
 * Safety Rules:
 * - Structural transformation only.
 * - Enforces immutable is_hypothetical: true marker.
 * - Strictly respects readerChapter as authoritative temporal firewall.
 * - Zero mutation of canonical objects.
 */

export interface FormattedHypotheticalImpact {
  id: string;
  entityName: string;
  entityType: 'CHARACTER' | 'POWER' | 'RELATIONSHIP' | 'SKILL';
  changedProperty: string;
  canonicalValue: string;
  hypotheticalValue: string;
  significance: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  isHypothetical: true;
}

export interface FormattedComparisonSummary {
  fromChapter: number;
  toChapter: number;
  charactersIntroduced: number;
  charactersRemoved: number;
  powerChanges: number;
  skillsUnlocked: number;
  relationshipsChanged: number;
  totalChanges: number;
  isHypothetical: true;
}

/**
 * Transforms backend TemporalComparisonResponse into formatted hypothetical impact rows.
 */
export function adaptHypotheticalImpacts(
  comparison: TemporalComparisonResponse | undefined | null,
  scenario: CounterfactualScenarioDTO | null
): FormattedHypotheticalImpact[] {
  if (!comparison) return [];

  const impacts: FormattedHypotheticalImpact[] = [];

  // 1. Character Status / Existence Diffs
  if (Array.isArray(comparison.character_changes)) {
    comparison.character_changes.forEach((c: CharacterDiffDTO) => {
      impacts.push({
        id: `char-${c.character_id}`,
        entityName: c.character_id,
        entityType: 'CHARACTER',
        changedProperty: 'Status / Existence',
        canonicalValue: c.before_status || 'Unintroduced',
        hypotheticalValue: c.after_status || 'Removed / Inactive',
        significance: c.change_type === 'REMOVED' || c.after_status === 'dead' ? 'CRITICAL' : 'HIGH',
        isHypothetical: true,
      });
    });
  }

  // 2. Power / Rank Diffs
  if (Array.isArray(comparison.power_changes)) {
    comparison.power_changes.forEach((p: PowerDiffDTO) => {
      impacts.push({
        id: `power-${p.character_id}`,
        entityName: p.character_id,
        entityType: 'POWER',
        changedProperty: 'Rank Progression',
        canonicalValue: p.before_rank || 'None',
        hypotheticalValue: p.after_rank || 'None',
        significance: 'HIGH',
        isHypothetical: true,
      });
    });
  }

  // 3. Relationship Diffs
  if (Array.isArray(comparison.relationship_changes)) {
    comparison.relationship_changes.forEach((r: RelationshipDiffDTO) => {
      impacts.push({
        id: `rel-${r.source_id}-${r.target_id}`,
        entityName: `${r.source_id} ↔ ${r.target_id}`,
        entityType: 'RELATIONSHIP',
        changedProperty: 'Allegiance / Affinity',
        canonicalValue: r.before_type || 'None',
        hypotheticalValue: r.after_type || 'Ended / Inverted',
        significance: 'CRITICAL',
        isHypothetical: true,
      });
    });
  }

  // 4. Skill Diffs
  if (Array.isArray(comparison.skill_changes)) {
    comparison.skill_changes.forEach((s: SkillDiffDTO) => {
      impacts.push({
        id: `skill-${s.character_id}`,
        entityName: s.character_id,
        entityType: 'SKILL',
        changedProperty: 'Unlocked Skills',
        canonicalValue: 'Standard Progression',
        hypotheticalValue: s.unlocked_skills.join(', ') || 'Altered Skills',
        significance: 'MEDIUM',
        isHypothetical: true,
      });
    });
  }

  // If scenario injected an intervention not fully caught in delta, synthesize explicitly stamped row
  if (scenario && impacts.length === 0) {
    impacts.push({
      id: `hypothetical-${scenario.scenario_id}`,
      entityName: scenario.assumption.target_entity_name || scenario.assumption.target_entity_id || 'Scenario Target',
      entityType: 'CHARACTER',
      changedProperty: scenario.assumption.assumption_type.replace(/_/g, ' '),
      canonicalValue: 'Canonical Lore',
      hypotheticalValue: scenario.assumption.proposed_value || 'Hypothetical Divergence',
      significance: 'CRITICAL',
      isHypothetical: true,
    });
  }

  return impacts;
}

/**
 * Builds a deterministic counterfactual scenario object with safety markers.
 */
export function buildCounterfactualScenario(
  seriesId: string,
  readerChapter: number,
  assumption: CounterfactualAssumption,
  baseComparison: TemporalComparisonResponse | null
): CounterfactualScenarioDTO {
  const scenarioHash = `${seriesId}-ch${readerChapter}-${assumption.assumption_type}-${assumption.target_chapter}-${assumption.target_entity_id || 'none'}`;

  const stateDivergence: TemporalComparisonResponse = baseComparison || {
    from_chapter: Math.max(1, assumption.target_chapter - 1),
    to_chapter: readerChapter,
    summary: {
      characters_introduced: 0,
      characters_removed: assumption.assumption_type === 'PREVENT_EVENT' ? 1 : 0,
      power_changes: assumption.assumption_type === 'ALTER_OUTCOME' ? 1 : 0,
      skills_unlocked: 0,
      relationships_changed: 1,
    },
    character_changes: [
      {
        character_id: assumption.target_entity_name || assumption.target_entity_id || 'Subject',
        change_type: assumption.assumption_type === 'PREVENT_EVENT' ? 'REMOVED' : 'CHANGED',
        before_status: 'Canonical State',
        after_status: assumption.proposed_value || 'Hypothetical Alternative',
      },
    ],
    power_changes: [],
    relationship_changes: [],
    skill_changes: [],
  };

  return {
    scenario_id: `scenario-${scenarioHash}`,
    series_id: seriesId,
    base_chapter: assumption.target_chapter,
    reader_chapter: readerChapter,
    assumption,
    is_hypothetical: true,
    confidence_score: 0.9,
    invalidated_events: assumption.target_event_id ? [assumption.target_event_id] : [],
    state_divergence: stateDivergence,
    narrative_summary: `Hypothetical branch initiated at Chapter ${assumption.target_chapter} simulating: ${assumption.justification || assumption.assumption_type}.`,
  };
}
