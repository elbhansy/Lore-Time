import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from packages.domain.search.search_query import SearchQuery, SearchType

from ....repositories.sqlalchemy_search_repository import SQLAlchemySearchRepository
from ...application.graph.get_temporal_graph import GraphEntitiesProvider
from ...application.search.global_search import GlobalSearchUseCase
from ...dependencies.database import get_db
from ...dependencies.services import get_world_state_use_case
from ...schemas.search import SearchPageDTO, SearchSuggestionDTO

router = APIRouter(tags=["Search"])


def get_entities_provider() -> GraphEntitiesProvider:
    return GraphEntitiesProvider()


def get_global_search_uc(
    db: Session = Depends(get_db),
    ws_uc=Depends(get_world_state_use_case),
    provider=Depends(get_entities_provider),
) -> GlobalSearchUseCase:
    repo = SQLAlchemySearchRepository(db)
    return GlobalSearchUseCase(repo, ws_uc, provider)


@router.get("/series/{series_id}/search", response_model=SearchPageDTO)
def global_search(
    series_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    type: SearchType = Query(SearchType.ALL),
    chapter: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    use_case: GlobalSearchUseCase = Depends(get_global_search_uc),
):
    query = SearchQuery(
        text=q, type=type, reader_chapter=chapter, page=page, page_size=page_size
    )
    page_result = use_case.execute(series_id, query)

    # Map domain to DTO
    return {
        "items": [
            {
                "id": str(item.id),
                "type": item.type,
                "title": item.title,
                "description": item.description,
                "relevance": item.relevance,
                "metadata": item.metadata,
            }
            for item in page_result.items
        ],
        "page": page_result.page,
        "page_size": page_result.page_size,
        "total": page_result.total,
        "has_next": page_result.has_next,
    }


@router.get(
    "/series/{series_id}/search/suggestions", response_model=list[SearchSuggestionDTO]
)
def search_suggestions(
    series_id: uuid.UUID,
    q: str = Query(..., min_length=1),
    chapter: int = Query(..., ge=1),
    use_case: GlobalSearchUseCase = Depends(get_global_search_uc),
):
    # For suggestions, we just do a lightweight global search and return top 5 titles
    query = SearchQuery(
        text=q, type=SearchType.ALL, reader_chapter=chapter, page=1, page_size=5
    )
    page_result = use_case.execute(series_id, query)

    return [
        {"id": str(item.id), "type": item.type, "title": item.title}
        for item in page_result.items
    ]
