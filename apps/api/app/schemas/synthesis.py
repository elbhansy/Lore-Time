"""Pydantic Transport DTOs for Temporal Narrative Causal Synthesis (Phase 5.3)."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class SynthesisConflictDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    conflict_id: str
    series_id: str
    target_event_id: str
    conflicting_relation_ids: list[str]
    conflict_type: str
    evidence_summary: str
    resolution_status: str


class NarrativeCausalStepDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    step_id: str
    series_id: str
    chapter: int
    source_event_id: str
    target_event_id: str
    relation_type: str
    derivation_type: str
    confidence: str
    affected_entities: list[str]
    state_change_summary: str
    impact_dimensions: list[str]
    arc_milestone_id: str | None = None
    turning_point_id: str | None = None
    phase_transition: str | None = None
    evidence_rule_id: str | None = None
    explanation_code: str | None = None


class NarrativeCausalPathDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    path_id: str
    series_id: str
    root_event_id: str
    terminal_event_id: str
    start_chapter: int
    end_chapter: int
    depth: int
    cumulative_impact_score: float
    impact_dimensions: list[str]
    steps: list[NarrativeCausalStepDTO]


class TurningPointSynthesisDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    turning_point_id: str
    character_id: str
    chapter: int
    trigger_event_id: str
    turning_point_type: str
    significance: str
    before_state: dict[str, Any]
    after_state: dict[str, Any]
    phase_before_id: str | None
    phase_after_id: str | None
    causal_root_event_ids: list[str]
    downstream_effect_event_ids: list[str]
    narrative_impact_summary: str


class TemporalNarrativeCausalExplanationDTO(BaseModel):
    model_config = ConfigDict(frozen=True)

    explanation_id: str
    series_id: str
    explanation_type: str
    reader_chapter: int
    focus_id: str
    headline: str
    narrative_steps: list[NarrativeCausalStepDTO]
    narrative_paths: list[NarrativeCausalPathDTO]
    turning_point_syntheses: list[TurningPointSynthesisDTO]
    intersected_milestone_ids: list[str]
    conflicts: list[SynthesisConflictDTO]
    impact_breakdown: dict[str, int]
    summary: dict[str, Any]
