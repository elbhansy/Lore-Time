from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

# --- Projection Contract ---


class ProjectionContract:
    """
    Defines which event types are expected to produce graph projections.
    Events not in this set are valid even with zero relationships.
    """

    GRAPH_PRODUCING_TYPES: set[str] = {
        "RELATIONSHIP_CHANGED",
        "POWER_RANK_CHANGED",
        "ALLIANCE_FORMED",
        "ALLIANCE_BROKEN",
        "COMBAT",
        "JOINED_FACTION",
        "LEFT_FACTION",
    }

    GRAPH_PROJECTION_VERSION: int = 1

    @classmethod
    def produces_graph_projection(cls, event_type: str) -> bool:
        return event_type in cls.GRAPH_PRODUCING_TYPES


# --- Issue Types ---


class IssueType(str, Enum):
    MISSING_RELATIONSHIP = "MISSING_RELATIONSHIP"
    ORPHAN_RELATIONSHIP = "ORPHAN_RELATIONSHIP"
    INVALID_EVENT_REF = "INVALID_EVENT_REF"
    DUPLICATE_PROJECTION = "DUPLICATE_PROJECTION"


@dataclass(frozen=True)
class ProjectionIssue:
    type: IssueType
    event_id: str = ""
    relationship_id: str = ""
    details: str = ""


# --- Report ---


@dataclass(frozen=True)
class ProjectionReport:
    scan_started_at: datetime
    scan_completed_at: datetime
    projection_version: int
    total_events: int
    total_entities: int
    total_relationships: int
    issues: list[ProjectionIssue]
    repair_applied: bool = False

    @property
    def issues_count(self) -> int:
        return len(self.issues)

    @property
    def is_consistent(self) -> bool:
        return self.issues_count == 0


# --- Abstract Interfaces (Reusable for future projections) ---


class ProjectionIntegrityChecker(ABC):
    @abstractmethod
    def check_integrity(self, series_id: str) -> ProjectionReport:
        pass


class ProjectionRebuilder(ABC):
    @abstractmethod
    def rebuild(self, series_id: str, dry_run: bool = True) -> ProjectionReport:
        pass
