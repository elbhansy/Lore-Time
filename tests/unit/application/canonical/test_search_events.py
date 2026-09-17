from datetime import datetime

from apps.api.app.application.canonical.search.search_events_use_case import (
    SearchEventsUseCase,
)
from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.paginated_response import PaginatedResponse
from packages.domain.canonical.search.canonical_search_query import CanonicalSearchQuery


class MockCanonicalSearchReader:
    def __init__(self, events):
        self.events = events

    def search_events(
        self, query: CanonicalSearchQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        results = []
        for e in self.events:
            if query.series_id != e.series_id:
                continue
            if query.event_type and query.event_type != e.type:
                continue

            # Simple mock for relevance search text matching
            if query.q:
                # Mock arbitrary relevance rank based on whether text matches
                if query.q.lower() in e.subject_id.lower():
                    # We inject a mock rank purely for test sorting purposes
                    results.append((e, 1.0))
                elif query.q.lower() in e.payload.get("text", "").lower():
                    results.append((e, 0.5))
            else:
                results.append((e, 0.0))

        # Rank deterministically: rank -> chapter_number -> sequence -> id
        results.sort(key=lambda item: (-item[1], item[0].chapter_number, 0, item[0].id))

        # Paginate
        dtos = [r[0] for r in results]
        offset = (query.page - 1) * query.limit
        page_items = dtos[offset : offset + query.limit]
        has_next = (offset + query.limit) < len(dtos)

        return PaginatedResponse(
            items=page_items,
            page=query.page,
            limit=query.limit,
            total=len(dtos),
            has_next=has_next,
        )


def test_search_relevance_and_deterministic_ordering():
    ev_a = CanonicalEventDTO(
        "A", "s1", "c1", 1, "COMBAT", "John", None, {}, {}, datetime.now()
    )
    ev_b = CanonicalEventDTO(
        "B", "s1", "c1", 1, "DIALOGUE", "John", None, {}, {}, datetime.now()
    )
    # C doesn't have John in subject_id, but has it in payload (lower relevance)
    ev_c = CanonicalEventDTO(
        "C",
        "s1",
        "c2",
        2,
        "COMBAT",
        "Alice",
        None,
        {"text": "John hit Alice"},
        {},
        datetime.now(),
    )

    reader = MockCanonicalSearchReader([ev_a, ev_b, ev_c])
    use_case = SearchEventsUseCase(reader)

    # Query 'John' (All 3 match, but A & B are higher relevance. Deterministic tie-breaker for A vs B: chapter -> sequence -> id. A comes before B alphabetically).
    res = use_case.execute(CanonicalSearchQuery(series_id="s1", q="John"))

    assert res.total == 3
    # A and B have relevance 1.0, C has 0.5. A vs B tie-breaker sorts by ID ("A" < "B")
    assert res.items[0].id == "A"
    assert res.items[1].id == "B"
    assert res.items[2].id == "C"


def test_search_combined_filters():
    ev_a = CanonicalEventDTO(
        "A", "s1", "c1", 1, "COMBAT", "John", None, {}, {}, datetime.now()
    )
    ev_b = CanonicalEventDTO(
        "B", "s1", "c1", 1, "DIALOGUE", "John", None, {}, {}, datetime.now()
    )

    reader = MockCanonicalSearchReader([ev_a, ev_b])
    use_case = SearchEventsUseCase(reader)

    # Query 'John' + type='COMBAT' -> Should only return A
    res = use_case.execute(
        CanonicalSearchQuery(series_id="s1", q="John", event_type="COMBAT")
    )

    assert res.total == 1
    assert res.items[0].id == "A"
