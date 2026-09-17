import uuid

from fastapi import APIRouter, Depends, Query

from ...application.exceptions import ResourceNotFound
from ...application.graph.get_temporal_graph import GraphEntitiesProvider
from ...application.skills.get_character_skills import GetCharacterSkillsUseCase
from ...application.skills.get_skill_evolution import GetSkillEvolutionUseCase
from ...application.skills.get_skill_explorer import GetSkillExplorerUseCase
from ...dependencies.services import get_world_state_use_case
from ...schemas.skills import (
    SkillEvolutionDTO,
    SkillExplorerItemDTO,
    SkillProgressionDTO,
)

router = APIRouter(tags=["Skills"])


def get_entities_provider() -> GraphEntitiesProvider:
    return GraphEntitiesProvider()


def get_skill_explorer_use_case(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetSkillExplorerUseCase(ws_uc, provider)


def get_character_skills_use_case(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetCharacterSkillsUseCase(ws_uc, provider)


def get_skill_evolution_use_case(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetSkillEvolutionUseCase(ws_uc, provider)


@router.get("/series/{series_id}/skills", response_model=list[SkillExplorerItemDTO])
def get_skills(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    use_case: GetSkillExplorerUseCase = Depends(get_skill_explorer_use_case),
):
    return use_case.execute(series_id, chapter)


@router.get(
    "/series/{series_id}/characters/{character_id}/skills",
    response_model=SkillProgressionDTO,
)
def get_character_skills(
    series_id: uuid.UUID,
    character_id: str,
    chapter: int = Query(..., ge=1),
    use_case: GetCharacterSkillsUseCase = Depends(get_character_skills_use_case),
):
    return use_case.execute(series_id, character_id, chapter)


@router.get(
    "/series/{series_id}/skills/{skill_id}/evolution", response_model=SkillEvolutionDTO
)
def get_skill_evolution(
    series_id: uuid.UUID,
    skill_id: str,
    chapter: int = Query(..., ge=1),
    use_case: GetSkillEvolutionUseCase = Depends(get_skill_evolution_use_case),
):
    try:
        return use_case.execute(series_id, skill_id, chapter)
    except ValueError as e:
        raise ResourceNotFound(str(e))
