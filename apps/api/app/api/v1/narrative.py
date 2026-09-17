"""Narrative Intelligence API Router (Phase 5.1).

Exposes Character Arc analysis endpoint conforming to the Phase 5.0 API contract.
"""

import uuid

from fastapi import APIRouter, Depends, Query

from apps.api.app.application.narrative.get_character_arc import GetCharacterArcUseCase
from apps.api.app.dependencies.services import get_character_arc_use_case
from apps.api.app.schemas.narrative import (
    ArcMilestoneDTO,
    ArcTrajectorySummaryDTO,
    CharacterArcResponse,
    NarrativePhaseDTO,
    TurningPointDTO,
)

router = APIRouter(prefix="/series", tags=["Narrative Intelligence"])


@router.get(
    "/{series_id}/intelligence/character-arc/{character_id}",
    response_model=CharacterArcResponse,
)
def get_character_arc(
    series_id: uuid.UUID,
    character_id: str,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    use_case: GetCharacterArcUseCase = Depends(get_character_arc_use_case),
):
    """Retrieves the deterministic, spoiler-free Character Arc for a character up to the reader's chapter horizon."""
    arc = use_case.execute(series_id, character_id, chapter)

    # Map Domain aggregate to DTO
    milestone_dtos = [
        ArcMilestoneDTO(
            milestone_id=m.milestone_id,
            character_id=m.character_id,
            chapter=m.chapter,
            sequence=m.sequence,
            event_id=m.event_id,
            milestone_type=m.milestone_type.value,
            description=m.description,
            previous_state=m.previous_state,
            new_state=m.new_state,
            is_canonical=m.is_canonical,
        )
        for m in arc.milestones
    ]

    tp_dtos = [
        TurningPointDTO(
            turning_point_id=t.turning_point_id,
            character_id=t.character_id,
            chapter=t.chapter,
            sequence=t.sequence,
            event_id=t.event_id,
            turning_point_type=t.turning_point_type.value,
            significance=t.significance.value,
            description=t.description,
            affected_dimensions=t.affected_dimensions,
            previous_state=t.previous_state,
            resulting_state=t.resulting_state,
            is_analytical=t.is_analytical,
        )
        for t in arc.turning_points
    ]

    phase_dtos = [
        NarrativePhaseDTO(
            phase_id=p.phase_id,
            character_id=p.character_id,
            phase_number=p.phase_number,
            title=p.title,
            from_chapter=p.from_chapter,
            to_chapter=p.to_chapter,
            milestone_ids=p.milestone_ids,
            turning_point_id=p.turning_point_id,
            dominant_faction=p.dominant_faction,
            rank_at_phase_end=p.rank_at_phase_end,
            is_active_at_horizon=p.is_active_at_horizon,
        )
        for p in arc.phases
    ]

    traj_dto = (
        ArcTrajectorySummaryDTO(
            total_milestones=arc.trajectory.total_milestones,
            total_turning_points=arc.trajectory.total_turning_points,
            total_phases=arc.trajectory.total_phases,
            current_status=arc.trajectory.current_status,
            current_rank=arc.trajectory.current_rank,
            current_faction=arc.trajectory.current_faction,
            total_skills_unlocked=arc.trajectory.total_skills_unlocked,
            total_relationships=arc.trajectory.total_relationships,
            highest_significance=arc.trajectory.highest_significance.value,
        )
        if arc.trajectory
        else None
    )

    return CharacterArcResponse(
        series_id=arc.series_id,
        character_id=arc.character_id,
        reader_chapter=arc.reader_chapter,
        start_chapter=arc.start_chapter,
        end_chapter=arc.end_chapter,
        milestones=milestone_dtos,
        turning_points=tp_dtos,
        phases=phase_dtos,
        trajectory=traj_dto,
    )
