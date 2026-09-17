from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.paginated_response import PaginatedResponse
from packages.domain.canonical.search.canonical_search_query import CanonicalSearchQuery
from packages.domain.canonical.search.canonical_search_reader import (
    CanonicalSearchReader,
)


class SearchEventsUseCase:
    def __init__(self, reader: CanonicalSearchReader):
        self.reader = reader

    def execute(
        self, query: CanonicalSearchQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        # Authorization and Security checks would go here.
        # Ensure the user has permission to view search results for query.series_id
        return self.reader.search_events(query)
