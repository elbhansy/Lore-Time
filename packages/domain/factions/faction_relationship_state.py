from dataclasses import dataclass


@dataclass
class FactionRelationshipState:
    subject_faction_id: str
    target_faction_id: str
    relationship_type: str
    active: bool
    started_at: int
    ended_at: int | None = None
