import uuid

from fastapi import APIRouter, Depends, Query

from packages.domain.analytics.analytics_reader import AnalyticsReader

from ...application.analytics.get_analytics_use_case import GetAnalyticsUseCase
from ...dependencies.database import get_db
from ...dependencies.repositories import get_series_repository
from ...schemas.analytics import (
    AnalyticsOverviewResponse,
    CharacterActivityResponse,
    EventDistributionDTO,
    RelationshipAnalyticsResponse,
)

router = APIRouter(prefix="/series/{series_id}/analytics", tags=["Analytics"])


def _to_distribution(buckets) -> list[EventDistributionDTO]:
    return [EventDistributionDTO(key=b.key, count=b.count) for b in buckets]


def get_analytics_reader(db=Depends(get_db)) -> AnalyticsReader:
    from apps.api.repositories.canonical.sqlalchemy_analytics_reader import (
        SQLAlchemyAnalyticsReader,
    )

    return SQLAlchemyAnalyticsReader(db)


def get_analytics_use_case(
    reader: AnalyticsReader = Depends(get_analytics_reader),
    series_repo=Depends(get_series_repository),
) -> GetAnalyticsUseCase:
    return GetAnalyticsUseCase(reader, series_repo)


@router.get("/overview", response_model=AnalyticsOverviewResponse)
def analytics_overview(
    series_id: uuid.UUID,
    from_chapter: int | None = Query(None, alias="from", ge=1),
    to_chapter: int | None = Query(None, alias="to", ge=1),
    use_case: GetAnalyticsUseCase = Depends(get_analytics_use_case),
):
    statistics = use_case.get_overview(series_id, from_chapter, to_chapter)
    return AnalyticsOverviewResponse(
        series_id=str(series_id),
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        statistics={
            "total_events": statistics.total_events,
            "chapters": statistics.chapters,
            "events_by_chapter": _to_distribution(statistics.events_by_chapter),
            "events_by_type": _to_distribution(statistics.events_by_type),
            "events_by_sequence": _to_distribution(statistics.events_by_sequence),
            "events_by_entity": _to_distribution(statistics.events_by_entity),
        },
    )


@router.get("/events", response_model=AnalyticsOverviewResponse)
def analytics_events(
    series_id: uuid.UUID,
    from_chapter: int | None = Query(None, alias="from", ge=1),
    to_chapter: int | None = Query(None, alias="to", ge=1),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    use_case: GetAnalyticsUseCase = Depends(get_analytics_use_case),
):
    # M3.0.2 event statistics are scope-level aggregates; pagination params
    # are accepted for contract stability but bucket counts cover full scope.
    statistics = use_case.get_overview(series_id, from_chapter, to_chapter)
    return AnalyticsOverviewResponse(
        series_id=str(series_id),
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        statistics={
            "total_events": statistics.total_events,
            "chapters": statistics.chapters,
            "events_by_chapter": _to_distribution(statistics.events_by_chapter),
            "events_by_type": _to_distribution(statistics.events_by_type),
            "events_by_sequence": _to_distribution(statistics.events_by_sequence),
            "events_by_entity": _to_distribution(statistics.events_by_entity),
        },
    )


@router.get("/entities/{entity_id}", response_model=list[CharacterActivityResponse])
def analytics_entity_activity(
    series_id: uuid.UUID,
    entity_id: str,
    from_chapter: int | None = Query(None, alias="from", ge=1),
    to_chapter: int | None = Query(None, alias="to", ge=1),
    limit: int = Query(50, ge=1, le=100),
    use_case: GetAnalyticsUseCase = Depends(get_analytics_use_case),
):
    metrics = use_case.get_entity_activity(
        series_id, entity_id, from_chapter, to_chapter, limit
    )
    return [
        CharacterActivityResponse(
            entity_id=m.entity_id,
            event_count=m.event_count,
            subject_count=m.subject_count,
            target_count=m.target_count,
            relationship_count=m.relationship_count,
            chapters_present=m.chapters_present,
            first_seen_chapter=m.first_seen_chapter,
            last_seen_chapter=m.last_seen_chapter,
        )
        for m in metrics
    ]


@router.get("/relationships", response_model=RelationshipAnalyticsResponse)
def analytics_relationships(
    series_id: uuid.UUID,
    from_chapter: int | None = Query(None, alias="from", ge=1),
    to_chapter: int | None = Query(None, alias="to", ge=1),
    limit: int = Query(50, ge=1, le=100),
    use_case: GetAnalyticsUseCase = Depends(get_analytics_use_case),
):
    ra = use_case.get_relationship_analytics(series_id, from_chapter, to_chapter, limit)
    return RelationshipAnalyticsResponse(
        frequency=[
            {
                "entity_id": f.entity_id,
                "relationship_type": f.relationship_type,
                "count": f.count,
            }
            for f in ra.frequency
        ],
        most_connected=_to_distribution(ra.most_connected),
        interaction_frequency=_to_distribution(ra.interaction_frequency),
        changes_by_chapter=[
            {
                "chapter_number": d.chapter_number,
                "created": d.created,
                "changed": d.changed,
                "ended": d.ended,
            }
            for d in ra.changes_by_chapter
        ],
    )
