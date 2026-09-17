/**
 * Phase 6.1 Frontend Read Model Contracts.
 * 
 * Typed frontend representations mirroring backend schemas in apps/api/app/schemas/read_models.py
 * and associated narrative, causal, and synthesis DTOs.
 * 
 * RULE: Must mirror backend read models. Do NOT invent fields or client-side intelligence calculations.
 */

export interface PaginationMeta {
  limit: number;
  offset: number;
  total_count: number;
  has_more: boolean;
}

export interface TemporalContextReadModel {
  series_id: string;
  reader_chapter: number;
  min_visible_chapter: number;
  max_visible_chapter: number;
  future_information_excluded: boolean;
}

export interface UniversalGraphNode {
  id: string;
  node_type: 'CHARACTER' | 'FACTION' | 'EVENT' | 'SKILL' | 'POWER_SYSTEM' | string;
  label: string;
  chapter?: number | null;
  metadata: Record<string, unknown>;
}

export interface UniversalGraphEdge {
  edge_id: string;
  source_id: string;
  target_id: string;
  edge_type: 'CAUSAL' | 'RELATIONSHIP' | 'AFFILIATION' | 'POWER_FLOW' | string;
  label: string;
  chapter?: number | null;
  weight: number;
  evidence_summary?: string | null;
  metadata: Record<string, unknown>;
}

export interface GenericGraphReadModel {
  temporal_context: TemporalContextReadModel;
  nodes: UniversalGraphNode[];
  edges: UniversalGraphEdge[];
}

export interface CausalEvidenceDTO {
  rule_id: string;
  explanation_code: string;
  source_event_ids: string[];
  target_event_id: string;
  temporal_basis: string;
  state_basis?: string | null;
  relationship_basis?: string | null;
  metadata: Record<string, unknown>;
}

export interface CausalRelationDTO {
  relation_id: string;
  series_id: string;
  source_event_id: string;
  target_event_id: string;
  relation_type: string;
  derivation_type: string;
  confidence: string;
  source_chapter: number;
  target_chapter: number;
  impact_score: number;
  affected_entity_ids: string[];
  evidence: CausalEvidenceDTO;
  metadata: Record<string, unknown>;
}

export interface ArcMilestoneDTO {
  milestone_id: string;
  character_id: string;
  chapter: number;
  sequence: number;
  event_id: string;
  milestone_type: string;
  description: string;
  previous_state: Record<string, unknown>;
  new_state: Record<string, unknown>;
  is_canonical: boolean;
}

export interface TurningPointDTO {
  turning_point_id: string;
  character_id: string;
  chapter: number;
  sequence: number;
  event_id: string;
  turning_point_type: string;
  significance: string;
  description: string;
  affected_dimensions: string[];
  previous_state: Record<string, unknown>;
  resulting_state: Record<string, unknown>;
  is_analytical: boolean;
}

export interface NarrativePhaseDTO {
  phase_id: string;
  character_id: string;
  phase_number: int_or_number;
  title: string;
  from_chapter: number;
  to_chapter: number;
  milestone_ids: string[];
  turning_point_id?: string | null;
  dominant_faction?: string | null;
  rank_at_phase_end?: string | null;
  is_active_at_horizon: boolean;
}
type int_or_number = number;

export interface EventReadModel {
  event_id: string;
  series_id: string;
  chapter_number: number;
  sequence: number;
  event_type: string;
  subject_type: string;
  subject_id: string;
  target_type?: string | null;
  target_id?: string | null;
  title: string;
  description: string;
  previous_state: Record<string, unknown>;
  new_state: Record<string, unknown>;
  metadata: Record<string, unknown>;
  causes: CausalRelationDTO[];
  effects: CausalRelationDTO[];
  is_milestone: boolean;
  is_turning_point: boolean;
}

export interface TimelineReadModel {
  temporal_context: TemporalContextReadModel;
  from_chapter: number;
  to_chapter: number;
  events: EventReadModel[];
  total_events: number;
  milestones: ArcMilestoneDTO[];
  turning_points: TurningPointDTO[];
  pagination: PaginationMeta;
}

export interface CharacterReadModel {
  character_id: string;
  series_id: string;
  name: string;
  temporal_context: TemporalContextReadModel;
  status: 'alive' | 'dead' | 'unintroduced' | string;
  rank?: string | null;
  faction_id?: string | null;
  unlocked_skills: string[];
  active_relationships_count: number;
  total_milestones_reached: number;
  total_turning_points_passed: number;
  current_phase_title?: string | null;
  milestones: ArcMilestoneDTO[];
  turning_points: TurningPointDTO[];
  phases: NarrativePhaseDTO[];
}

export interface StoryOverviewReadModel {
  series_id: string;
  series_title: string;
  temporal_context: TemporalContextReadModel;
  total_chapters_visible: number;
  total_events_visible: number;
  total_characters_visible: number;
  total_factions_visible: number;
  total_relationships_active: number;
  recent_turning_points: TurningPointDTO[];
  recent_events: EventReadModel[];
  active_phases_by_character: Record<string, string>;
}

export interface NarrativeCausalStepDTO {
  step_id: string;
  series_id: string;
  chapter: number;
  source_event_id: string;
  target_event_id: string;
  relation_type: string;
  derivation_type: string;
  confidence: string;
  affected_entities: string[];
  state_change_summary: string;
  impact_dimensions: string[];
  arc_milestone_id?: string | null;
  turning_point_id?: string | null;
  phase_transition?: string | null;
  evidence_rule_id?: string | null;
  explanation_code?: string | null;
}

export interface NarrativeCausalPathDTO {
  path_id: string;
  series_id: string;
  root_event_id: string;
  terminal_event_id: string;
  start_chapter: number;
  end_chapter: number;
  depth: number;
  cumulative_impact_score: number;
  impact_dimensions: string[];
  steps: NarrativeCausalStepDTO[];
}

export interface TurningPointSynthesisDTO {
  turning_point_id: string;
  character_id: string;
  chapter: number;
  trigger_event_id: string;
  turning_point_type: string;
  significance: string;
  before_state: Record<string, unknown>;
  after_state: Record<string, unknown>;
  phase_before_id?: string | null;
  phase_after_id?: string | null;
  causal_root_event_ids: string[];
  downstream_effect_event_ids: string[];
  narrative_impact_summary: string;
}

export interface SynthesisConflictDTO {
  conflict_id: string;
  series_id: string;
  target_event_id: string;
  conflicting_relation_ids: string[];
  conflict_type: string;
  evidence_summary: string;
  resolution_status: string;
}

export interface TemporalNarrativeCausalExplanationDTO {
  explanation_id: string;
  series_id: string;
  explanation_type: string;
  reader_chapter: number;
  focus_id: string;
  headline: string;
  narrative_steps: NarrativeCausalStepDTO[];
  narrative_paths: NarrativeCausalPathDTO[];
  turning_point_syntheses: TurningPointSynthesisDTO[];
  intersected_milestone_ids: string[];
  conflicts: SynthesisConflictDTO[];
  impact_breakdown: Record<string, number>;
  summary: Record<string, unknown>;
}

export interface ArcTrajectorySummaryDTO {
  total_milestones: number;
  total_turning_points: number;
  total_phases: number;
  current_status: string;
  current_rank?: string | null;
  current_faction?: string | null;
  total_skills_unlocked: number;
  total_relationships: number;
  highest_significance: string;
}

export interface CharacterArcResponse {
  series_id: string;
  character_id: string;
  reader_chapter: number;
  start_chapter?: number | null;
  end_chapter?: number | null;
  milestones: ArcMilestoneDTO[];
  turning_points: TurningPointDTO[];
  phases: NarrativePhaseDTO[];
  trajectory?: ArcTrajectorySummaryDTO | null;
}

export interface CharacterDiffDTO {
  character_id: string;
  change_type: string;
  before_status?: string | null;
  after_status?: string | null;
}

export interface PowerDiffDTO {
  character_id: string;
  before_rank?: string | null;
  after_rank?: string | null;
}

export interface RelationshipDiffDTO {
  source_id: string;
  target_id: string;
  change_type: string;
  before_type?: string | null;
  after_type?: string | null;
}

export interface SkillDiffDTO {
  character_id: string;
  unlocked_skills: string[];
}

export interface TemporalComparisonResponse {
  from_chapter: number;
  to_chapter: number;
  summary: {
    characters_introduced?: number;
    characters_removed?: number;
    power_changes?: number;
    skills_unlocked?: number;
    relationships_changed?: number;
    [key: string]: number | undefined;
  };
  character_changes: CharacterDiffDTO[];
  power_changes: PowerDiffDTO[];
  relationship_changes: RelationshipDiffDTO[];
  skill_changes: SkillDiffDTO[];
}

export type AssumptionType = 'PREVENT_EVENT' | 'ALTER_OUTCOME' | 'INJECT_EVENT';

export interface CounterfactualAssumption {
  target_event_id?: string | null;
  target_chapter: number;
  assumption_type: AssumptionType;
  target_entity_id?: string | null;
  target_entity_name?: string | null;
  proposed_value?: string | null;
  justification: string;
}

export interface CounterfactualScenarioDTO {
  scenario_id: string;
  series_id: string;
  base_chapter: number;
  reader_chapter: number;
  assumption: CounterfactualAssumption;
  is_hypothetical: true;
  confidence_score: number;
  invalidated_events: string[];
  state_divergence: TemporalComparisonResponse;
  narrative_summary: string;
}
