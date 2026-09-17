from abc import ABC, abstractmethod

from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.canonical_event_query import CanonicalEventQuery
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


class CanonicalEventReader(ABC):
    @abstractmethod
    def get_timeline(
        self, query: CanonicalEventQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        pass
