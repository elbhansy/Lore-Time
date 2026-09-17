"""UI-Facing Read Models and Query Transfer Objects (Phase 5.4).

Exposes unified, stable, deterministic read models for UI consumption across:
- TemporalContextReadModel: Consistent temporal horizon and spoiler metadata.
- PaginationMeta: Bounded pagination controls.
- GenericGraphReadModel (GraphNode, GraphEdge): Universal visualization contract.
- EventReadModel: Comprehensive event projection with impacts, causes, and state changes.
- CharacterReadModel: Character projection with state, arc, and relationships at chapter horizon.
- TimelineReadModel: Chronological feed with events, state deltas, and milestone markers.
- StoryOverviewReadModel: High-level dashboard aggregate for a series at a reader chapter.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.schemas.causality import CausalRelationDTO
from apps.api.app.schemas.narrative import (
    ArcMilestoneDTO,
    NarrativePhaseDTO,
    TurningPointDTO,
)


class PaginationMeta(BaseModel):
    """Deterministic pagination metadata."""

    model_config = ConfigDict(frozen=True)

    limit: int
    offset: int
    total_count: int
    has_more: bool


class TemporalContextReadModel(BaseModel):
    """Shared, consistent temporal boundary metadata."""

    model_config = ConfigDict(frozen=True)

    series_id: str
    reader_chapter: int
    min_visible_chapter: int = 1
    max_visible_chapter: int
    future_information_excluded: bool = True


class UniversalGraphNode(BaseModel):
    """Universal node contract for frontend graph visualization."""

    model_config = ConfigDict(frozen=True)

    id: str
    node_type: str  # "CHARACTER", "FACTION", "EVENT", "SKILL", "POWER_SYSTEM"
    label: str
    chapter: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class UniversalGraphEdge(BaseModel):
    """Universal directed edge contract for frontend graph visualization."""

    model_config = ConfigDict(frozen=True)

    edge_id: str
    source_id: str
    target_id: str
    edge_type: str  # "CAUSAL", "RELATIONSHIP", "AFFILIATION", "POWER_FLOW"
    label: str
    chapter: int | None = None
    weight: float = 1.0
    evidence_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenericGraphReadModel(BaseModel):
    """Universal graph model for frontend network visualizers."""

    model_config = ConfigDict(frozen=True)

    temporal_context: TemporalContextReadModel
    nodes: list[UniversalGraphNode]
    edges: list[UniversalGraphEdge]


class EventReadModel(BaseModel):
    """Comprehensive UI read model for a single event."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    series_id: str
    chapter_number: int
    sequence: int
    event_type: str
    subject_type: str
    subject_id: str
    target_type: str | None = None
    target_id: str | None = None
    title: str
    description: str
    previous_state: dict[str, Any] = Field(default_factory=dict)
    new_state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    causes: list[CausalRelationDTO] = Field(default_factory=list)
    effects: list[CausalRelationDTO] = Field(default_factory=list)
    is_milestone: bool = False
    is_turning_point: bool = False


class TimelineReadModel(BaseModel):
    """Chronological event feed with temporal bounds and pagination."""

    model_config = ConfigDict(frozen=True)

    temporal_context: TemporalContextReadModel
    from_chapter: int
    to_chapter: int
    events: list[EventReadModel]
    total_events: int
    milestones: list[ArcMilestoneDTO] = Field(default_factory=list)
    turning_points: list[TurningPointDTO] = Field(default_factory=list)
    pagination: PaginationMeta


class CharacterReadModel(BaseModel):
    """Comprehensive UI read model for a character at a specific chapter horizon."""

    model_config = ConfigDict(frozen=True)

    character_id: str
    series_id: str
    name: str
    temporal_context: TemporalContextReadModel
    status: str  # "alive", "dead", "unintroduced"
    rank: str | None = None
    faction_id: str | None = None
    unlocked_skills: list[str] = Field(default_factory=list)
    active_relationships_count: int = 0
    total_milestones_reached: int = 0
    total_turning_points_passed: int = 0
    current_phase_title: str | None = None
    milestones: list[ArcMilestoneDTO] = Field(default_factory=list)
    turning_points: list[TurningPointDTO] = Field(default_factory=list)
    phases: list[NarrativePhaseDTO] = Field(default_factory=list)


class StoryOverviewReadModel(BaseModel):
    """High-level dashboard summary of an entire story series at a reader chapter."""

    model_config = ConfigDict(frozen=True)

    series_id: str
    series_title: str
    temporal_context: TemporalContextReadModel
    total_chapters_visible: int
    total_events_visible: int
    total_characters_visible: int
    total_factions_visible: int
    total_relationships_active: int
    recent_turning_points: list[TurningPointDTO] = Field(default_factory=list)
    recent_events: list[EventReadModel] = Field(default_factory=list)
    active_phases_by_character: dict[str, str] = Field(default_factory=dict)
