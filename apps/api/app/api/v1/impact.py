import uuid

from fastapi import APIRouter, Depends, Query

from packages.domain.services.event_applier import EventApplier
from packages.domain.services.event_impact_analyzer import EventImpactAnalyzer

from ...application.impact.get_event_impact import GetEventImpactUseCase
from ...application.impact.get_impact_timeline import GetImpactTimelineUseCase
from ...dependencies.services import get_event_repository, get_world_state_use_case
from ...schemas.impact import EventImpactDTO, ImpactAnalysisResultDTO

router = APIRouter(tags=["Impacts"])


# Dependency factory
def get_event_impact_analyzer() -> EventImpactAnalyzer:
    return EventImpactAnalyzer(EventApplier())


def get_event_impact_use_case(
    event_repo=Depends(get_event_repository),
    ws_uc=Depends(get_world_state_use_case),
    analyzer: EventImpactAnalyzer = Depends(get_event_impact_analyzer),
) -> GetEventImpactUseCase:
    return GetEventImpactUseCase(event_repo, ws_uc, analyzer)


def get_impact_timeline_use_case(
    event_repo=Depends(get_event_repository),
    ws_uc=Depends(get_world_state_use_case),
    analyzer: EventImpactAnalyzer = Depends(get_event_impact_analyzer),
) -> GetImpactTimelineUseCase:
    return GetImpactTimelineUseCase(event_repo, ws_uc, analyzer)


def map_impact_result(result) -> ImpactAnalysisResultDTO:
    return ImpactAnalysisResultDTO(
        event_id=result.event_id,
        chapter=result.chapter,
        affected_entities=result.affected_entities,
        impacts=[
            EventImpactDTO(
                event_id=i.event_id,
                chapter_number=i.chapter_number,
                event_type=i.event_type,
                impact_type=i.impact_type.value,
                affected_entity_id=i.affected_entity_id,
                description_key=i.description_key,
                details=i.details,
            )
            for i in result.impacts
        ],
    )


@router.get(
    "/series/{series_id}/events/{event_id}/impact",
    response_model=ImpactAnalysisResultDTO,
)
def get_event_impact(
    series_id: uuid.UUID,
    event_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    use_case: GetEventImpactUseCase = Depends(get_event_impact_use_case),
):
    result = use_case.execute(series_id, event_id, chapter)
    return map_impact_result(result)


@router.get(
    "/series/{series_id}/impact-timeline", response_model=list[ImpactAnalysisResultDTO]
)
def get_impact_timeline(
    series_id: uuid.UUID,
    from_chapter: int = Query(..., ge=1),
    to_chapter: int = Query(..., ge=1),
    reader_chapter: int = Query(..., ge=1),
    use_case: GetImpactTimelineUseCase = Depends(get_impact_timeline_use_case),
):
    results = use_case.execute(series_id, from_chapter, to_chapter, reader_chapter)
    return [map_impact_result(r) for r in results]
