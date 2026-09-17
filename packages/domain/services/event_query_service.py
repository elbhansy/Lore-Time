from packages.domain.events.event_query import EventQuery
from packages.domain.events.event_query_result import EventQueryResult
from packages.domain.repositories.event_repository import EventRepository


class EventQueryService:
    def __init__(self, repository: EventRepository):
        self.repository = repository

    def query(self, q: EventQuery) -> EventQueryResult:
        # Domain validation is already handled by EventQuery.__post_init__
        # to_chapter <= reader_chapter is strictly enforced there.

        # 1. Fetch filtered and canonically ordered candidates directly from repository
        items = self.repository.query(q)

        # 2. Get total count for pagination
        total = self.repository.count(q)

        # 3. Calculate has_next
        end_idx = q.page * q.page_size
        has_next = end_idx < total

        return EventQueryResult(
            reader_chapter=q.reader_chapter,
            from_chapter=q.from_chapter,
            to_chapter=q.to_chapter,
            items=items,
            page=q.page,
            page_size=q.page_size,
            total=total,
            has_next=has_next,
        )
