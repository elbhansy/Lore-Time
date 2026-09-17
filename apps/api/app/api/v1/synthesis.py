"""Temporal Narrative Causal Synthesis API Router (Phase 5.3).

Exposes:
- GET /api/v1/series/{series_id}/intelligence/event-narrative/{event_id}
- GET /api/v1/series/{series_id}/intelligence/character-narrative-causality/{character_id}
"""

import uuid

from fastapi import APIRouter, Depends, Query

from apps.api.app.application.synthesis.get_narrative_synthesis import (
    GetCharacterNarrativeCausalityUseCase,
    GetEventNarrativeExplanationUseCase,
)
from apps.api.app.dependencies.services import (
    get_character_narrative_causality_use_case,
    get_event_narrative_use_case,
)
from apps.api.app.schemas.synthesis import (
    NarrativeCausalPathDTO,
    NarrativeCausalStepDTO,
    SynthesisConflictDTO,
    TemporalNarrativeCausalExplanationDTO,
    TurningPointSynthesisDTO,
)
from packages.domain.synthesis.models import TemporalNarrativeCausalExplanation

router = APIRouter(prefix="/series", tags=["Temporal Narrative Synthesis"])


def _map_explanation_dto(
    exp: TemporalNarrativeCausalExplanation,
) -> TemporalNarrativeCausalExplanationDTO:
    step_dtos = [
        NarrativeCausalStepDTO(
            step_id=s.step_id,
            series_id=s.series_id,
            chapter=s.chapter,
            source_event_id=s.source_event_id,
            target_event_id=s.target_event_id,
            relation_type=s.relation_type.value,
            derivation_type=s.derivation_type.value,
            confidence=s.confidence.value,
            affected_entities=list(s.affected_entities),
            state_change_summary=s.state_change_summary,
            impact_dimensions=[d.value for d in s.impact_dimensions],
            arc_milestone_id=s.arc_milestone_id,
            turning_point_id=s.turning_point_id,
            phase_transition=s.phase_transition,
            evidence_rule_id=s.evidence_rule_id,
            explanation_code=s.explanation_code,
        )
        for s in exp.narrative_steps
    ]

    path_dtos = [
        NarrativeCausalPathDTO(
            path_id=p.path_id,
            series_id=p.series_id,
            root_event_id=p.root_event_id,
            terminal_event_id=p.terminal_event_id,
            start_chapter=p.start_chapter,
            end_chapter=p.end_chapter,
            depth=p.depth,
            cumulative_impact_score=p.cumulative_impact_score,
            impact_dimensions=[d.value for d in p.impact_dimensions],
            steps=[
                NarrativeCausalStepDTO(
                    step_id=st.step_id,
                    series_id=st.series_id,
                    chapter=st.chapter,
                    source_event_id=st.source_event_id,
                    target_event_id=st.target_event_id,
                    relation_type=st.relation_type.value,
                    derivation_type=st.derivation_type.value,
                    confidence=st.confidence.value,
                    affected_entities=list(st.affected_entities),
                    state_change_summary=st.state_change_summary,
                    impact_dimensions=[d.value for d in st.impact_dimensions],
                )
                for st in p.steps
            ],
        )
        for p in exp.narrative_paths
    ]

    tp_dtos = [
        TurningPointSynthesisDTO(
            turning_point_id=t.turning_point_id,
            character_id=t.character_id,
            chapter=t.chapter,
            trigger_event_id=t.trigger_event_id,
            turning_point_type=t.turning_point_type,
            significance=t.significance,
            before_state=t.before_state,
            after_state=t.after_state,
            phase_before_id=t.phase_before_id,
            phase_after_id=t.phase_after_id,
            causal_root_event_ids=list(t.causal_root_event_ids),
            downstream_effect_event_ids=list(t.downstream_effect_event_ids),
            narrative_impact_summary=t.narrative_impact_summary,
        )
        for t in exp.turning_point_syntheses
    ]

    conflict_dtos = [
        SynthesisConflictDTO(
            conflict_id=c.conflict_id,
            series_id=c.series_id,
            target_event_id=c.target_event_id,
            conflicting_relation_ids=list(c.conflicting_relation_ids),
            conflict_type=c.conflict_type,
            evidence_summary=c.evidence_summary,
            resolution_status=c.resolution_status.value,
        )
        for c in exp.conflicts
    ]

    return TemporalNarrativeCausalExplanationDTO(
        explanation_id=exp.explanation_id,
        series_id=exp.series_id,
        explanation_type=exp.explanation_type.value,
        reader_chapter=exp.reader_chapter,
        focus_id=exp.focus_id,
        headline=exp.headline,
        narrative_steps=step_dtos,
        narrative_paths=path_dtos,
        turning_point_syntheses=tp_dtos,
        intersected_milestone_ids=list(exp.intersected_milestone_ids),
        conflicts=conflict_dtos,
        impact_breakdown=exp.impact_breakdown,
        summary=exp.summary,
    )


@router.get(
    "/{series_id}/intelligence/event-narrative/{event_id}",
    response_model=TemporalNarrativeCausalExplanationDTO,
)
def get_event_narrative_explanation(
    series_id: uuid.UUID,
    event_id: str,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    max_depth: int = Query(
        4, ge=1, le=10, description="Maximum causal exploration depth"
    ),
    use_case: GetEventNarrativeExplanationUseCase = Depends(
        get_event_narrative_use_case
    ),
):
    """Retrieves deterministic temporal narrative explanation for an event."""
    exp = use_case.execute(
        series_id=series_id,
        event_id=event_id,
        reader_chapter=chapter,
        max_depth=max_depth,
    )
    return _map_explanation_dto(exp)


@router.get(
    "/{series_id}/intelligence/character-narrative-causality/{character_id}",
    response_model=TemporalNarrativeCausalExplanationDTO,
)
def get_character_narrative_causality(
    series_id: uuid.UUID,
    character_id: str,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    max_depth: int = Query(
        4, ge=1, le=10, description="Maximum causal exploration depth"
    ),
    use_case: GetCharacterNarrativeCausalityUseCase = Depends(
        get_character_narrative_causality_use_case
    ),
):
    """Retrieves deterministic character arc milestones, turning points, and causal triggers."""
    exp = use_case.execute(
        series_id=series_id,
        character_id=character_id,
        reader_chapter=chapter,
        max_depth=max_depth,
    )
    return _map_explanation_dto(exp)
