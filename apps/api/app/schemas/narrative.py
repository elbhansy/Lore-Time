"""Schemas and DTOs for Narrative Intelligence and Character Arc (Phase 5.1)."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ArcMilestoneDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    milestone_id: str
    character_id: str
    chapter: int
    sequence: int
    event_id: str
    milestone_type: str
    description: str
    previous_state: dict[str, Any] = Field(default_factory=dict)
    new_state: dict[str, Any] = Field(default_factory=dict)
    is_canonical: bool = True


class TurningPointDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    turning_point_id: str
    character_id: str
    chapter: int
    sequence: int
    event_id: str
    turning_point_type: str
    significance: str
    description: str
    affected_dimensions: list[str]
    previous_state: dict[str, Any] = Field(default_factory=dict)
    resulting_state: dict[str, Any] = Field(default_factory=dict)
    is_analytical: bool = True


class NarrativePhaseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    phase_id: str
    character_id: str
    phase_number: int
    title: str
    from_chapter: int
    to_chapter: int
    milestone_ids: list[str] = Field(default_factory=list)
    turning_point_id: str | None = None
    dominant_faction: str | None = None
    rank_at_phase_end: str | None = None
    is_active_at_horizon: bool = False


class ArcTrajectorySummaryDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_milestones: int
    total_turning_points: int
    total_phases: int
    current_status: str
    current_rank: str | None = None
    current_faction: str | None = None
    total_skills_unlocked: int
    total_relationships: int
    highest_significance: str


class CharacterArcResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    series_id: str
    character_id: str
    reader_chapter: int
    start_chapter: int | None = None
    end_chapter: int | None = None
    milestones: list[ArcMilestoneDTO] = Field(default_factory=list)
    turning_points: list[TurningPointDTO] = Field(default_factory=list)
    phases: list[NarrativePhaseDTO] = Field(default_factory=list)
    trajectory: ArcTrajectorySummaryDTO | None = None
