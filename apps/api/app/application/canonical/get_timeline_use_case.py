from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.canonical_event_query import CanonicalEventQuery
from packages.domain.canonical.queries.canonical_event_reader import (
    CanonicalEventReader,
)
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


class GetTimelineUseCase:
    def __init__(self, reader: CanonicalEventReader):
        self.reader = reader

    def execute(
        self, query: CanonicalEventQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        # Authorization and Security checks would go here.
        # e.g., Verify user has access to query.series_id

        return self.reader.get_timeline(query)
