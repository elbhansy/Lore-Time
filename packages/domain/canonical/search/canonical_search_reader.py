from abc import ABC, abstractmethod

from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.paginated_response import PaginatedResponse
from packages.domain.canonical.search.canonical_search_query import CanonicalSearchQuery


class CanonicalSearchReader(ABC):
    @abstractmethod
    def search_events(
        self, query: CanonicalSearchQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        pass
