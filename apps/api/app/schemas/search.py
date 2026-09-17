from typing import Any

from pydantic import BaseModel, Field

from packages.domain.search.search_type import SearchType


class SearchQueryDTO(BaseModel):
    q: str
    type: SearchType = SearchType.ALL
    chapter: int = Field(ge=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class SearchResultDTO(BaseModel):
    id: str
    type: SearchType
    title: str
    description: str | None = None
    relevance: float
    metadata: dict[str, Any]


class SearchPageDTO(BaseModel):
    items: list[SearchResultDTO]
    page: int
    page_size: int
    total: int
    has_next: bool


class SearchSuggestionDTO(BaseModel):
    id: str
    type: SearchType
    title: str
