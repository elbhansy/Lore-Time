"""Temporal Narrative Causal Synthesis Domain Models & Contracts (Phase 5.3).

Synthesizes:
- Canonical Events
- WorldState
- Temporal Relationships
- Character Arcs & Milestones (Phase 5.1)
- Causal Relations & Multi-Hop Chains (Phase 5.2)

into a structured, deterministic temporal causal narrative explanation.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from packages.domain.causality.models import (
    CausalConfidence,
    CausalConflict,
    CausalDerivationType,
    CausalRelationType,
)


class NarrativeExplanationType(StrEnum):
    """Scope and focus of the temporal narrative causal explanation."""

    EVENT_NARRATIVE = "EVENT_NARRATIVE"
    CHARACTER_NARRATIVE = "CHARACTER_NARRATIVE"
    ARC_NARRATIVE = "ARC_NARRATIVE"


class NarrativeImpactDimension(StrEnum):
    """Categorization of where and how a causal event alters the narrative."""

    CHARACTER_IMPACT = "CHARACTER_IMPACT"
    RELATIONSHIP_IMPACT = "RELATIONSHIP_IMPACT"
    FACTION_IMPACT = "FACTION_IMPACT"
    POWER_IMPACT = "POWER_IMPACT"
    STATE_IMPACT = "STATE_IMPACT"
    ARC_IMPACT = "ARC_IMPACT"
    TEMPORAL_IMPACT = "TEMPORAL_IMPACT"


@dataclass(frozen=True)
class NarrativeCausalStep:
    """Represents an atomic link in the causal narrative progression:

    Cause -> Event / State Change -> Effect -> Character/Faction/Power Impact -> Narrative Consequence.
    """

    step_id: str
    series_id: str
    chapter: int
    source_event_id: str
    target_event_id: str
    relation_type: CausalRelationType
    derivation_type: CausalDerivationType
    confidence: CausalConfidence
    affected_entities: tuple[str, ...]
    state_change_summary: str
    impact_dimensions: tuple[NarrativeImpactDimension, ...]
    arc_milestone_id: str | None = None
    turning_point_id: str | None = None
    phase_transition: str | None = None
    evidence_rule_id: str | None = None
    explanation_code: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "series_id": self.series_id,
            "chapter": self.chapter,
            "source_event_id": self.source_event_id,
            "target_event_id": self.target_event_id,
            "relation_type": self.relation_type.value,
            "derivation_type": self.derivation_type.value,
            "confidence": self.confidence.value,
            "affected_entities": list(self.affected_entities),
            "state_change_summary": self.state_change_summary,
            "impact_dimensions": [d.value for d in self.impact_dimensions],
            "arc_milestone_id": self.arc_milestone_id,
            "turning_point_id": self.turning_point_id,
            "phase_transition": self.phase_transition,
            "evidence_rule_id": self.evidence_rule_id,
            "explanation_code": self.explanation_code,
        }


@dataclass(frozen=True)
class NarrativeCausalPath:
    """Ordered path of causal steps connecting a root cause to a narrative consequence."""

    path_id: str
    series_id: str
    root_event_id: str
    terminal_event_id: str
    start_chapter: int
    end_chapter: int
    steps: tuple[NarrativeCausalStep, ...]
    cumulative_impact_score: float
    depth: int
    impact_dimensions: tuple[NarrativeImpactDimension, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "path_id": self.path_id,
            "series_id": self.series_id,
            "root_event_id": self.root_event_id,
            "terminal_event_id": self.terminal_event_id,
            "start_chapter": self.start_chapter,
            "end_chapter": self.end_chapter,
            "depth": self.depth,
            "cumulative_impact_score": round(self.cumulative_impact_score, 4),
            "impact_dimensions": [d.value for d in self.impact_dimensions],
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass(frozen=True)
class TurningPointSynthesis:
    """Synthesizes a narrative turning point with its causal trigger, state delta, and arc consequence."""

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
    causal_root_event_ids: tuple[str, ...]
    downstream_effect_event_ids: tuple[str, ...]
    narrative_impact_summary: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "turning_point_id": self.turning_point_id,
            "character_id": self.character_id,
            "chapter": self.chapter,
            "trigger_event_id": self.trigger_event_id,
            "turning_point_type": self.turning_point_type,
            "significance": self.significance,
            "before_state": dict(self.before_state),
            "after_state": dict(self.after_state),
            "phase_before_id": self.phase_before_id,
            "phase_after_id": self.phase_after_id,
            "causal_root_event_ids": list(self.causal_root_event_ids),
            "downstream_effect_event_ids": list(self.downstream_effect_event_ids),
            "narrative_impact_summary": self.narrative_impact_summary,
        }


@dataclass(frozen=True)
class TemporalNarrativeCausalExplanation:
    """Root aggregate representing complete synthesized temporal causal narrative explanation."""

    explanation_id: str
    series_id: str
    explanation_type: NarrativeExplanationType
    reader_chapter: int
    focus_id: str  # event_id or character_id
    headline: str
    narrative_steps: tuple[NarrativeCausalStep, ...]
    narrative_paths: tuple[NarrativeCausalPath, ...]
    turning_point_syntheses: tuple[TurningPointSynthesis, ...]
    intersected_milestone_ids: tuple[str, ...]
    conflicts: tuple[CausalConflict, ...]
    impact_breakdown: dict[str, int]
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "series_id": self.series_id,
            "explanation_type": self.explanation_type.value,
            "reader_chapter": self.reader_chapter,
            "focus_id": self.focus_id,
            "headline": self.headline,
            "narrative_steps": [s.to_dict() for s in self.narrative_steps],
            "narrative_paths": [p.to_dict() for p in self.narrative_paths],
            "turning_point_syntheses": [
                tp.to_dict() for tp in self.turning_point_syntheses
            ],
            "intersected_milestone_ids": list(self.intersected_milestone_ids),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "impact_breakdown": dict(self.impact_breakdown),
            "summary": dict(self.summary),
        }
