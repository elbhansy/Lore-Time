from pydantic import BaseModel


class EventImpactDTO(BaseModel):
    event_id: str
    chapter_number: int
    event_type: str
    impact_type: str
    affected_entity_id: str
    description_key: str
    details: dict | None = None


class ImpactAnalysisResultDTO(BaseModel):
    event_id: str
    chapter: int
    impacts: list[EventImpactDTO]
    affected_entities: list[str]
