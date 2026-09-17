export interface FactionExplorerItemDTO {
  id: string;
  name: string;
  member_count: number;
  introduced_chapter: number;
}

export interface FactionProfileDTO {
  id: string;
  name: string;
  description?: string;
  introduced_chapter: number;
  member_count: number;
  leader_id?: string;
  leader_name?: string;
  active_relationships_count: number;
}

export interface FactionMemberDTO {
  character_id: string;
  name: string;
  rank: string | null;
  joined_chapter: number;
  is_active: boolean;
}

export interface FactionLeadershipDTO {
  leader_id: string;
  leader_name: string;
  active: boolean;
  started_at: number;
  ended_at?: number;
}
