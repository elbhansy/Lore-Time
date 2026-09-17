from dataclasses import dataclass
from enum import Enum


class ResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    AMBIGUOUS = "AMBIGUOUS"


@dataclass
class ResolutionResult:
    status: ResolutionStatus
    entity_id: str | None = None
    confidence: float = 0.0
    matched_alias: str | None = None


@dataclass
class EntityAlias:
    id: str
    series_id: str
    entity_id: str
    entity_type: str
    alias: str
    normalized_alias: str
    source: str | None = None
    confidence: float = 1.0
    active: bool = True
