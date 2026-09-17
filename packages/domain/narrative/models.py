"""Narrative Intelligence Domain Models and Value Objects (Phase 5.1).

Defines:
- MilestoneType: Supported discrete milestone types.
- ArcMilestone: Significant canonical state transition for a character.
- SignificanceLevel: Deterministic significance categorization (LOW, MEDIUM, HIGH, CRITICAL).
- TurningPointType: Type of major structural narrative turning point.
- TurningPoint: Analytically significant narrative transition.
- NarrativePhase: Contiguous temporal segment bounded by turning points or arc horizons.
- CharacterArc: Complete synthesized temporal evolution aggregate for a character up to readerChapter.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class MilestoneType(StrEnum):
    FIRST_APPEARANCE = "FIRST_APPEARANCE"
    DEATH = "DEATH"
    RESURRECTION = "RESURRECTION"
    RANK_CHANGE = "RANK_CHANGE"
    SKILL_ACQUIRED = "SKILL_ACQUIRED"
    SKILL_EVOLVED = "SKILL_EVOLVED"
    SKILL_LOST = "SKILL_LOST"
    FACTION_JOINED = "FACTION_JOINED"
    FACTION_LEFT = "FACTION_LEFT"
    FACTION_LEADERSHIP = "FACTION_LEADERSHIP"
    RELATIONSHIP_FORMED = "RELATIONSHIP_FORMED"
    RELATIONSHIP_CHANGED = "RELATIONSHIP_CHANGED"
    RELATIONSHIP_SEVERED = "RELATIONSHIP_SEVERED"
    MAJOR_EVENT = "MAJOR_EVENT"


class SignificanceLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TurningPointType(StrEnum):
    MORTALITY_EVENT = "MORTALITY_EVENT"  # Death or resurrection
    POWER_BREAKTHROUGH = "POWER_BREAKTHROUGH"  # Rank jump or high-tier skill evolution
    FACTION_REALIGNMENT = (
        "FACTION_REALIGNMENT"  # Joining, leaving, or leading a faction
    )
    RELATIONSHIP_TRANSFORMATION = (
        "RELATIONSHIP_TRANSFORMATION"  # Critical allegiance swing (ally -> enemy)
    )
    MULTI_DIMENSIONAL_SHIFT = (
        "MULTI_DIMENSIONAL_SHIFT"  # 2+ state dimensions modified simultaneously
    )


@dataclass(frozen=True)
class ArcMilestone:
    """Represents a discrete, canonical state transition for a character."""

    milestone_id: str
    character_id: str
    chapter: int
    sequence: int
    event_id: str
    milestone_type: MilestoneType
    description: str
    previous_state: dict[str, Any] = field(default_factory=dict)
    new_state: dict[str, Any] = field(default_factory=dict)
    is_canonical: bool = True


@dataclass(frozen=True)
class TurningPoint:
    """Represents an analytically significant inflection point in a character's arc."""

    turning_point_id: str
    character_id: str
    chapter: int
    sequence: int
    event_id: str
    turning_point_type: TurningPointType
    significance: SignificanceLevel
    description: str
    affected_dimensions: list[str]
    previous_state: dict[str, Any] = field(default_factory=dict)
    resulting_state: dict[str, Any] = field(default_factory=dict)
    is_analytical: bool = True


@dataclass(frozen=True)
class NarrativePhase:
    """Represents a contiguous temporal segment in a character's evolution."""

    phase_id: str
    character_id: str
    phase_number: int
    title: str
    from_chapter: int
    to_chapter: int
    milestone_ids: list[str] = field(default_factory=list)
    turning_point_id: str | None = None
    dominant_faction: str | None = None
    rank_at_phase_end: str | None = None
    is_active_at_horizon: bool = False


@dataclass(frozen=True)
class ArcTrajectorySummary:
    """Deterministic quantitative summary of a character's arc."""

    total_milestones: int
    total_turning_points: int
    total_phases: int
    current_status: str  # "alive", "dead", "unintroduced"
    current_rank: str | None
    current_faction: str | None
    total_skills_unlocked: int
    total_relationships: int
    highest_significance: SignificanceLevel


@dataclass(frozen=True)
class CharacterArc:
    """Root aggregate representing the complete narrative arc of a character up to readerChapter."""

    series_id: str
    character_id: str
    reader_chapter: int
    start_chapter: int | None
    end_chapter: int | None
    milestones: list[ArcMilestone] = field(default_factory=list)
    turning_points: list[TurningPoint] = field(default_factory=list)
    phases: list[NarrativePhase] = field(default_factory=list)
    trajectory: ArcTrajectorySummary | None = None
