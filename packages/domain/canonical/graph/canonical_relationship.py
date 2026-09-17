from dataclasses import dataclass


@dataclass
class CanonicalRelationship:
    id: str
    series_id: str
    source_entity_id: str
    target_entity_id: str
    type: str  # e.g. KNOWS, ATTACKED
    event_id: str
    sequence: int
