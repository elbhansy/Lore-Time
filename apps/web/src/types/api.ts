export interface SeriesResponse {
  id: string;
  title: string;
  slug: string;
  total_chapters: number;
}

export interface CharacterStateResponse {
  exists: boolean;
  alive: boolean;
  rank: string | null;
  unlocked_skills: string[];
  faction_id: string | null;
}

export interface PowerSystemResponse {
  id: string;
  series_id: string;
  name: string;
  slug: string;
  description: string | null;
}

export interface RankResponse {
  id: string;
  power_system_id: string;
  name: string;
  slug: string;
  order: number;
  introduced_chapter: number;
  description: string | null;
  parent_rank_id: string | null;
}

export interface CharacterNode {
  id: string;
  name: string;
  rank: string | null;
  alive: boolean;
}

export interface RelationshipEdge {
  id: string;
  source: string;
  target: string;
  type: string;
  active: boolean;
}

export interface RelationshipGraphResponse {
  nodes: CharacterNode[];
  edges: RelationshipEdge[];
}

export interface CharacterGraphResponse {
  root_character_id: string;
  chapter: number;
  depth: number;
  nodes: CharacterNode[];
  edges: RelationshipEdge[];
}

export interface RelationshipHistoryEvent {
  chapter: number;
  type: string;
}

export interface RelationshipHistoryResponse {
  source_id: string;
  target_id: string;
  history: RelationshipHistoryEvent[];
}

export interface CharacterDiffDTO {
  character_id: string;
  change_type: 'INTRODUCED' | 'REMOVED' | 'CHANGED';
  before_status: string | null;
  after_status: string | null;
}

export interface PowerDiffDTO {
  character_id: string;
  before_rank: string | null;
  after_rank: string | null;
}

export interface RelationshipDiffDTO {
  source_id: string;
  target_id: string;
  change_type: 'CREATED' | 'ENDED' | 'CHANGED';
  before_type: string | null;
  after_type: string | null;
}

export interface SkillDiffDTO {
  character_id: string;
  unlocked_skills: string[];
}

export interface TemporalComparisonResponse {
  from_chapter: number;
  to_chapter: number;
  summary: {
    characters_introduced: number;
    characters_removed: number;
    power_changes: number;
    skills_unlocked: number;
    relationships_changed: number;
  };
  character_changes: CharacterDiffDTO[];
  power_changes: PowerDiffDTO[];
  relationship_changes: RelationshipDiffDTO[];
  skill_changes: SkillDiffDTO[];
}

export interface EventImpactDTO {
  event_id: string;
  chapter_number: number;
  event_type: string;
  impact_type: string;
  affected_entity_id: string;
  description_key: string;
  details: any | null;
}

export interface ImpactAnalysisResultDTO {
  event_id: string;
  chapter: number;
  impacts: EventImpactDTO[];
  affected_entities: string[];
}

export interface GraphNodeDTO {
  id: string;
  type: string;
  label: string;
  metadata?: any;
}

export interface GraphEdgeDTO {
  source_id: string;
  target_id: string;
  type: string;
  metadata?: any;
}

export interface TemporalGraphDTO {
  reader_chapter: number;
  nodes: GraphNodeDTO[];
  edges: GraphEdgeDTO[];
}

export interface CharacterResponse {
  id: string;
  name: string;
  state: CharacterStateResponse;
  as_of_chapter: number;
}

export interface RelationshipStateResponse {
  subject_id: string;
  target_id: string;
  relationship_type: string;
  active: boolean;
}

export interface WorldStateResponse {
  series_id: string;
  chapter: number;
  characters: Record<string, CharacterStateResponse>;
  factions: Record<string, any>;
  powers: Record<string, any>;
  relationships: RelationshipStateResponse[];
}

export interface EventResponse {
  id: string;
  chapter_number: number;
  sequence: number;
  type: string;
  subject_type: string;
  subject_id: string;
  target_type: string | null;
  target_id: string | null;
  metadata: Record<string, any>;
}
