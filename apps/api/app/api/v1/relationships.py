import uuid

from fastapi import APIRouter, Depends, Query

from ...application.relationships.get_character_graph import GetCharacterGraphUseCase
from ...application.relationships.get_relationship_graph import (
    GetRelationshipGraphUseCase,
)
from ...application.relationships.get_relationship_history import (
    GetRelationshipHistoryUseCase,
)
from ...dependencies.services import (
    get_character_graph_use_case,
    get_relationship_graph_use_case,
    get_relationship_history_use_case,
)
from ...schemas.relationship import (
    CharacterGraphResponse,
    RelationshipGraphResponse,
    RelationshipHistoryResponse,
)

router = APIRouter(tags=["Relationships"])


@router.get(
    "/series/{series_id}/relationship-graph", response_model=RelationshipGraphResponse
)
def get_relationship_graph(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1, description="Reader's chapter"),
    type: str | None = Query("ALL", description="Filter by relationship type"),
    use_case: GetRelationshipGraphUseCase = Depends(get_relationship_graph_use_case),
):
    return use_case.execute(series_id, chapter, type)


@router.get(
    "/series/{series_id}/characters/{character_id}/relationship-graph",
    response_model=CharacterGraphResponse,
)
def get_character_graph(
    series_id: uuid.UUID,
    character_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    depth: int = Query(1, ge=1, le=2),
    use_case: GetCharacterGraphUseCase = Depends(get_character_graph_use_case),
):
    return use_case.execute(series_id, character_id, chapter, depth)


@router.get(
    "/series/{series_id}/relationships/{source_id}/{target_id}/history",
    response_model=RelationshipHistoryResponse,
)
def get_relationship_history(
    series_id: uuid.UUID,
    source_id: uuid.UUID,
    target_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    use_case: GetRelationshipHistoryUseCase = Depends(
        get_relationship_history_use_case
    ),
):
    return use_case.execute(series_id, source_id, target_id, chapter)
