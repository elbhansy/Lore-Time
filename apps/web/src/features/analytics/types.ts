/**
 * Analytics DTOs — mirrors apps/api/app/schemas/analytics.py exactly.
 * UI consumes these shapes only (M3.0.6 rule).
 */

export interface EventDistributionDTO {
  key: string;
  count: number;
}

export interface EventStatisticsDTO {
  total_events: number;
  chapters: number;
  events_by_chapter: EventDistributionDTO[];
  events_by_type: EventDistributionDTO[];
  events_by_sequence: EventDistributionDTO[];
  events_by_entity: EventDistributionDTO[];
}

export interface AnalyticsOverviewDTO {
  series_id: string;
  from_chapter: number | null;
  to_chapter: number | null;
  statistics: EventStatisticsDTO;
}

export interface CharacterActivityDTO {
  entity_id: string;
  event_count: number;
  subject_count: number;
  target_count: number;
  relationship_count: number;
  chapters_present: number;
  first_seen_chapter: number | null;
  last_seen_chapter: number | null;
}

export interface RelationshipMetricDTO {
  entity_id: string;
  relationship_type: string;
  count: number;
}

export interface RelationshipChapterDeltaDTO {
  chapter_number: number;
  created: number;
  changed: number;
  ended: number;
}

export interface RelationshipAnalyticsDTO {
  frequency: RelationshipMetricDTO[];
  most_connected: EventDistributionDTO[];
  interaction_frequency: EventDistributionDTO[];
  changes_by_chapter: RelationshipChapterDeltaDTO[];
}
