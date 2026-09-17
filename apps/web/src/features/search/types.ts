export enum SearchType {
  ALL = 'ALL',
  CHARACTER = 'CHARACTER',
  FACTION = 'FACTION',
  POWER_SYSTEM = 'POWER_SYSTEM',
  RANK = 'RANK',
  SKILL = 'SKILL',
  EVENT = 'EVENT'
}

export interface SearchResultDTO {
  id: string;
  type: SearchType;
  title: string;
  description?: string;
  relevance: number;
  metadata: Record<string, any>;
}

export interface SearchPageDTO {
  items: SearchResultDTO[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}

export interface SearchSuggestionDTO {
  id: string;
  type: SearchType;
  title: string;
}
