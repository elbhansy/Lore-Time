import uuid

from fastapi import APIRouter, Depends, Query

from ...application.exceptions import ResourceNotFound
from ...application.power_system.get_power_systems import GetPowerSystemsUseCase
from ...application.power_system.get_rank_progression import GetRankProgressionUseCase
from ...application.power_system.get_ranks import GetRanksUseCase
from ...dependencies.services import (
    get_power_systems_use_case,
    get_rank_progression_use_case,
    get_ranks_use_case,
)
from ...schemas.power_system import PowerSystemResponse, RankResponse

router = APIRouter(tags=["Power Systems"])


@router.get(
    "/series/{series_id}/power-systems", response_model=list[PowerSystemResponse]
)
def get_power_systems(
    series_id: uuid.UUID,
    use_case: GetPowerSystemsUseCase = Depends(get_power_systems_use_case),
):
    systems = use_case.execute(series_id)
    return [
        PowerSystemResponse(
            id=str(ps.id.value),
            series_id=str(ps.series_id.value),
            name=ps.name,
            slug=ps.slug,
            description=ps.description,
        )
        for ps in systems
    ]


@router.get(
    "/series/{series_id}/power-systems/{power_system_id}/ranks",
    response_model=list[RankResponse],
)
def get_ranks(
    series_id: uuid.UUID,
    power_system_id: uuid.UUID,
    chapter: int = Query(
        ..., ge=1, description="Reader's chapter for spoiler firewall"
    ),
    use_case: GetRanksUseCase = Depends(get_ranks_use_case),
):
    try:
        ranks = use_case.execute(series_id, power_system_id, chapter)
        return [
            RankResponse(
                id=str(r.id.value),
                power_system_id=str(r.power_system_id.value),
                name=r.name,
                slug=r.slug,
                order=r.order,
                introduced_chapter=r.introduced_chapter.value,
                description=r.description,
                parent_rank_id=str(r.parent_rank_id.value)
                if r.parent_rank_id
                else None,
            )
            for r in ranks
        ]
    except ValueError as e:
        raise ResourceNotFound(str(e))


@router.get(
    "/series/{series_id}/characters/{character_id}/power-progression",
    response_model=list[RankResponse],
)
def get_rank_progression(
    series_id: uuid.UUID,
    character_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    use_case: GetRankProgressionUseCase = Depends(get_rank_progression_use_case),
):
    ranks = use_case.execute(series_id, character_id, chapter)
    return [
        RankResponse(
            id=str(r.id.value),
            power_system_id=str(r.power_system_id.value),
            name=r.name,
            slug=r.slug,
            order=r.order,
            introduced_chapter=r.introduced_chapter.value,
            description=r.description,
            parent_rank_id=str(r.parent_rank_id.value) if r.parent_rank_id else None,
        )
        for r in ranks
    ]
