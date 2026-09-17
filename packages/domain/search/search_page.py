from dataclasses import dataclass

from packages.domain.search.search_result import SearchResult


@dataclass
class SearchPage:
    items: list[SearchResult]
    page: int
    page_size: int
    total: int
    has_next: bool
