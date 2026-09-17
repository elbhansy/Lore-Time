from abc import ABC, abstractmethod

from packages.domain.search.search_query import SearchQuery
from packages.domain.search.search_result import SearchResult


class SearchRepository(ABC):
    @abstractmethod
    def search_candidates(
        self, query: SearchQuery, series_id: str
    ) -> list[SearchResult]:
        """
        Returns all possible candidates matching the text search from the database.
        It DOES NOT apply temporal visibility (reader_chapter).
        The returned candidates will be filtered by the Use Case.
        """
        pass
