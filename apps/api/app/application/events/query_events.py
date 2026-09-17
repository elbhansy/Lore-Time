from packages.domain.events.event_query import EventQuery
from packages.domain.events.event_query_result import EventQueryResult
from packages.domain.services.event_query_service import EventQueryService


class QueryEventsUseCase:
    def __init__(self, query_service: EventQueryService):
        self.query_service = query_service

    def execute(self, query: EventQuery) -> EventQueryResult:
        return self.query_service.query(query)
