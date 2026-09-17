from pydantic import BaseModel


class EventDistributionDTO(BaseModel):
    key: str
    count: int


class EventStatisticsResponse(BaseModel):
    total_events: int
    chapters: int
    events_by_chapter: list[EventDistributionDTO]
    events_by_type: list[EventDistributionDTO]
    events_by_sequence: list[EventDistributionDTO]
    events_by_entity: list[EventDistributionDTO]


class AnalyticsOverviewResponse(BaseModel):
    series_id: str
    from_chapter: int | None
    to_chapter: int | None
    statistics: EventStatisticsResponse


class CharacterActivityResponse(BaseModel):
    entity_id: str
    event_count: int
    subject_count: int
    target_count: int
    relationship_count: int
    chapters_present: int
    first_seen_chapter: int | None
    last_seen_chapter: int | None


class RelationshipMetricDTO(BaseModel):
    entity_id: str
    relationship_type: str
    count: int


class RelationshipChapterDeltaDTO(BaseModel):
    chapter_number: int
    created: int
    changed: int
    ended: int


class RelationshipAnalyticsResponse(BaseModel):
    frequency: list[RelationshipMetricDTO]
    most_connected: list[EventDistributionDTO]
    interaction_frequency: list[EventDistributionDTO]
    changes_by_chapter: list[RelationshipChapterDeltaDTO]


# Re-export so the route layer can build DTOs from domain metrics without
# importing pydantic types by hand-mapping every field.
def to_distribution(dtos) -> list[EventDistributionDTO]:
    return [EventDistributionDTO(key=b.key, count=b.count) for b in dtos]
