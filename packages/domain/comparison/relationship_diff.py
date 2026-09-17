from dataclasses import dataclass
from enum import Enum


class RelationshipChangeType(str, Enum):
    CREATED = "CREATED"
    ENDED = "ENDED"
    CHANGED = "CHANGED"


@dataclass(frozen=True)
class RelationshipDiff:
    source_id: str
    target_id: str
    change_type: RelationshipChangeType
    before_type: str | None
    after_type: str | None
