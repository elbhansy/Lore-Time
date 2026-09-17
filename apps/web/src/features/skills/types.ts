export interface SkillExplorerItemDTO {
  id: string;
  name: string;
  introduced_chapter: number;
  active_users_count: number;
}

export interface SkillProgressionDTO {
  active_skills: Array<{
    character_id: string;
    skill_id: string;
    skill_name?: string;
    active: boolean;
    unlocked_at: number;
    upgraded_at?: number;
    lost_at?: number;
  }>;
  relations: Array<{
    id: string;
    source_skill_id: string;
    target_skill_id: string;
    type: string;
    scope: string;
    character_id?: string;
    introduced_chapter?: number;
  }>;
}

export interface SkillEvolutionDTO {
  skill_id: string;
  nodes: Array<{
    id: string;
    name: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
  }>;
}
