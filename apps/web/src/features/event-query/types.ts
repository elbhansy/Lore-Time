export interface EventDTO {
  id: string;
  series_id: string;
  chapter_id: string;
  sequence: number;
  type: string;
  subject_type: string;
  subject_id: string;
  target_type: string | null;
  target_id: string | null;
  previous_state: Record<string, any>;
  new_state: Record<string, any>;
  metadata: Record<string, any>;
}

export interface EventQueryResultDTO {
  reader_chapter: number;
  from_chapter: number;
  to_chapter: number;
  items: EventDTO[];
  page: number;
  page_size: number;
  total: number;
  has_next: boolean;
}
