"""Read / Query API Router for UI Clients (Phase 5.4).

Exposes stable, UI-facing read endpoints:
- GET /api/v1/series/{series_id}/intelligence/overview
- GET /api/v1/series/{series_id}/intelligence/timeline-feed
- GET /api/v1/series/{series_id}/intelligence/characters/{character_id}/profile
- GET /api/v1/series/{series_id}/intelligence/graph
"""

import uuid

from fastapi import APIRouter, Depends, Query

from apps.api.app.application.intelligence.intelligence_query_service import (
    IntelligenceQueryService,
)
from apps.api.app.dependencies.services import get_intelligence_query_service
from apps.api.app.schemas.read_models import (
    CharacterReadModel,
    GenericGraphReadModel,
    StoryOverviewReadModel,
    TimelineReadModel,
)

router = APIRouter(prefix="/series", tags=["Intelligence Read Models"])


@router.get(
    "/{series_id}/intelligence/overview",
    response_model=StoryOverviewReadModel,
)
def get_story_overview(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    query_service: IntelligenceQueryService = Depends(get_intelligence_query_service),
):
    """Returns high-level story dashboard overview for a series at a reader chapter."""
    return query_service.get_story_overview(
        series_id=series_id,
        reader_chapter=chapter,
    )


@router.get(
    "/{series_id}/intelligence/timeline-feed",
    response_model=TimelineReadModel,
)
def get_timeline_feed(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    from_chapter: int = Query(1, alias="from", ge=1, description="Start chapter"),
    to_chapter: int | None = Query(None, alias="to", ge=1, description="End chapter"),
    limit: int = Query(50, ge=1, le=100, description="Page limit"),
    offset: int = Query(0, ge=0, description="Page offset"),
    query_service: IntelligenceQueryService = Depends(get_intelligence_query_service),
):
    """Returns a deterministic, paginated timeline feed with attached causes and effects."""
    return query_service.get_timeline(
        series_id=series_id,
        reader_chapter=chapter,
        from_chapter=from_chapter,
        to_chapter=to_chapter,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{series_id}/intelligence/characters/{character_id}/profile",
    response_model=CharacterReadModel,
)
def get_character_profile(
    series_id: uuid.UUID,
    character_id: str,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    query_service: IntelligenceQueryService = Depends(get_intelligence_query_service),
):
    """Returns a complete UI profile for a character at a chapter horizon."""
    return query_service.get_character_read_model(
        series_id=series_id,
        character_id=character_id,
        reader_chapter=chapter,
    )


@router.get(
    "/{series_id}/intelligence/graph",
    response_model=GenericGraphReadModel,
)
def get_intelligence_graph(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="Reader's current chapter horizon"),
    graph_type: str = Query(
        "causal", description="Type of graph ('causal' or 'relationship')"
    ),
    query_service: IntelligenceQueryService = Depends(get_intelligence_query_service),
):
    """Returns a universal graph projection (nodes + edges) for frontend visualizers."""
    return query_service.get_generic_graph(
        series_id=series_id,
        reader_chapter=chapter,
        graph_type=graph_type,
    )
