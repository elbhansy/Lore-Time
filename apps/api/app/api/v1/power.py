import uuid

from fastapi import APIRouter, Depends, Query

from ...application.graph.get_temporal_graph import GraphEntitiesProvider
from ...application.power.get_power_comparison import GetPowerComparisonUseCase
from ...application.power.get_power_progression import GetPowerProgressionUseCase
from ...application.power.get_rank_population import (
    GetRankDistributionUseCase,
    GetRankPopulationUseCase,
)
from ...dependencies.services import get_world_state_use_case
from ...schemas.power import (
    PowerComparisonDTO,
    PowerProgressionDTO,
    PowerSystemDistributionDTO,
)

router = APIRouter(tags=["Power"])


def get_entities_provider() -> GraphEntitiesProvider:
    return GraphEntitiesProvider()


def get_power_progression_uc(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetPowerProgressionUseCase(ws_uc, provider)


def get_rank_population_uc(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetRankPopulationUseCase(ws_uc, provider)


def get_rank_distribution_uc(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetRankDistributionUseCase(ws_uc, provider)


def get_power_comparison_uc(
    ws_uc=Depends(get_world_state_use_case), provider=Depends(get_entities_provider)
):
    return GetPowerComparisonUseCase(ws_uc, provider)


@router.get(
    "/series/{series_id}/characters/{character_id}/power-progression",
    response_model=PowerProgressionDTO,
)
def get_power_progression(
    series_id: uuid.UUID,
    character_id: str,
    power_system_id: str = Query(...),
    chapter: int = Query(..., ge=1),
    use_case: GetPowerProgressionUseCase = Depends(get_power_progression_uc),
):
    return use_case.execute(series_id, character_id, power_system_id, chapter)


@router.get(
    "/series/{series_id}/power-systems/{power_system_id}/distribution",
    response_model=PowerSystemDistributionDTO,
)
def get_rank_distribution(
    series_id: uuid.UUID,
    power_system_id: str,
    chapter: int = Query(..., ge=1),
    use_case: GetRankDistributionUseCase = Depends(get_rank_distribution_uc),
):
    return use_case.execute(series_id, power_system_id, chapter)


@router.get(
    "/series/{series_id}/power-systems/{power_system_id}/ranks/{rank_id}/characters",
    response_model=list[str],
)
def get_rank_population(
    series_id: uuid.UUID,
    power_system_id: str,
    rank_id: str,
    chapter: int = Query(..., ge=1),
    use_case: GetRankPopulationUseCase = Depends(get_rank_population_uc),
):
    return use_case.execute(series_id, power_system_id, rank_id, chapter)


@router.get("/series/{series_id}/power-comparison", response_model=PowerComparisonDTO)
def get_power_comparison(
    series_id: uuid.UUID,
    character_a: str = Query(...),
    character_b: str = Query(...),
    power_system_id: str = Query(...),
    chapter: int = Query(..., ge=1),
    use_case: GetPowerComparisonUseCase = Depends(get_power_comparison_uc),
):
    return use_case.execute(
        series_id, character_a, character_b, power_system_id, chapter
    )
