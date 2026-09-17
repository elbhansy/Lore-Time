import uuid

from fastapi import APIRouter, Depends, Query

from ...application.comparison.compare_world_states import CompareWorldStatesUseCase
from ...dependencies.services import get_world_state_use_case
from ...schemas.comparison import (
    CharacterDiffDTO,
    PowerDiffDTO,
    RelationshipDiffDTO,
    SkillDiffDTO,
    TemporalComparisonResponse,
)

router = APIRouter(tags=["Comparison"])


def get_compare_world_states_use_case(
    ws_uc=Depends(get_world_state_use_case),
) -> CompareWorldStatesUseCase:
    return CompareWorldStatesUseCase(ws_uc)


@router.get("/series/{series_id}/comparison", response_model=TemporalComparisonResponse)
def compare_world_states(
    series_id: uuid.UUID,
    from_chapter: int = Query(..., ge=1),
    to_chapter: int = Query(..., ge=1),
    reader_chapter: int = Query(..., ge=1),
    use_case: CompareWorldStatesUseCase = Depends(get_compare_world_states_use_case),
):
    comp = use_case.execute(series_id, from_chapter, to_chapter, reader_chapter)

    # Map Domain Model to DTO
    return TemporalComparisonResponse(
        from_chapter=comp.from_chapter,
        to_chapter=comp.to_chapter,
        summary=comp.summary,
        character_changes=[
            CharacterDiffDTO(**c.__dict__) for c in comp.character_changes
        ],
        power_changes=[PowerDiffDTO(**p.__dict__) for p in comp.power_changes],
        relationship_changes=[
            RelationshipDiffDTO(**r.__dict__) for r in comp.relationship_changes
        ],
        skill_changes=[SkillDiffDTO(**s.__dict__) for s in comp.skill_changes],
    )
