export interface RankDTO {
  id: string;
  name?: string;
  order?: number;
}

export interface RankTransitionDTO {
  from_rank_id?: string;
  from_rank_name?: string;
  to_rank_id: string;
  to_rank_name?: string;
  chapter: number;
  event_id: string;
  breakthrough_status: string;
}

export interface PowerProgressionDTO {
  character_id: string;
  power_system_id: string;
  current_rank?: RankDTO;
  transitions: RankTransitionDTO[];
}

export interface RankDistributionItemDTO {
  rank_id: string;
  rank_name: string;
  order: number;
  count: number;
}

export interface PowerSystemDistributionDTO {
  power_system_id: string;
  distribution: RankDistributionItemDTO[];
}

export interface PowerComparisonDTO {
  character_a: { rank?: string; order?: number };
  character_b: { rank?: string; order?: number };
  result: string;
}
