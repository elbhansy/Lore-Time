import uuid

from fastapi import APIRouter, Depends, Query

from ...application.graph.get_entity_neighborhood import GetEntityNeighborhoodUseCase
from ...application.graph.get_temporal_graph import (
    GetTemporalGraphUseCase,
    GraphEntitiesProvider,
)
from ...dependencies.services import get_world_state_use_case
from ...schemas.graph import GraphEdgeDTO, GraphNodeDTO, TemporalGraphDTO

router = APIRouter(tags=["Knowledge Graph"])


def get_graph_entities_provider() -> GraphEntitiesProvider:
    return GraphEntitiesProvider()


def get_temporal_graph_use_case(
    ws_uc=Depends(get_world_state_use_case),
    provider=Depends(get_graph_entities_provider),
) -> GetTemporalGraphUseCase:
    return GetTemporalGraphUseCase(ws_uc, provider)


def get_entity_neighborhood_use_case(
    temporal_graph_uc=Depends(get_temporal_graph_use_case),
) -> GetEntityNeighborhoodUseCase:
    return GetEntityNeighborhoodUseCase(temporal_graph_uc)


def map_graph(graph) -> TemporalGraphDTO:
    return TemporalGraphDTO(
        reader_chapter=graph.reader_chapter,
        nodes=[
            GraphNodeDTO(
                id=str(n.id), type=n.type.value, label=str(n.label), metadata=n.metadata
            )
            for n in graph.nodes
        ],
        edges=[
            GraphEdgeDTO(
                source_id=str(e.source_id),
                target_id=str(e.target_id),
                type=e.type.value,
                metadata=e.metadata,
            )
            for e in graph.edges
        ],
    )


@router.get("/series/{series_id}/graph", response_model=TemporalGraphDTO)
def get_temporal_graph(
    series_id: uuid.UUID,
    chapter: int = Query(..., ge=1),
    use_case: GetTemporalGraphUseCase = Depends(get_temporal_graph_use_case),
):
    graph = use_case.execute(series_id, chapter)
    return map_graph(graph)


@router.get(
    "/series/{series_id}/entities/{entity_id}/neighborhood",
    response_model=TemporalGraphDTO,
)
def get_entity_neighborhood(
    series_id: uuid.UUID,
    entity_id: str,
    chapter: int = Query(..., ge=1),
    depth: int = Query(1, ge=1, le=3),
    use_case: GetEntityNeighborhoodUseCase = Depends(get_entity_neighborhood_use_case),
):
    graph = use_case.execute(series_id, entity_id, chapter, depth)
    return map_graph(graph)
