from dataclasses import dataclass

from .impact_type import ImpactType


@dataclass(frozen=True)
class EventImpact:
    event_id: str
    chapter_number: int
    event_type: str
    impact_type: ImpactType
    affected_entity_id: str
    description_key: str  # e.g., "CHARACTER_DIED", "RANK_CHANGED", "RELATIONSHIP_ENDED"
    details: dict | None = None  # e.g. {"before": "A", "after": "S"}
