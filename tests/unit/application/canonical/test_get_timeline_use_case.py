from datetime import datetime

from apps.api.app.application.canonical.get_timeline_use_case import GetTimelineUseCase
from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.canonical_event_query import CanonicalEventQuery
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


class MockCanonicalEventReader:
    def __init__(self, dtos: list[CanonicalEventDTO]):
        # Mock simulating DB sorting logic
        self.dtos = sorted(dtos, key=lambda x: (x.chapter_number, 0, x.id))

    def get_timeline(
        self, query: CanonicalEventQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        offset = (query.page - 1) * query.limit
        page_items = self.dtos[offset : offset + query.limit]
        has_next = (offset + query.limit) < len(self.dtos)
        return PaginatedResponse(
            items=page_items,
            page=query.page,
            limit=query.limit,
            total=len(self.dtos),
            has_next=has_next,
        )


def generate_mock_events(count: int) -> list[CanonicalEventDTO]:
    events = []
    for i in range(count):
        events.append(
            CanonicalEventDTO(
                id=f"ev_{i}",
                series_id="s1",
                chapter_id="c1",
                chapter_number=i % 10,  # Distribute across chapters
                type="TEST_EVENT",
                subject_id="sub_1",
                target_id=None,
                payload={},
                provenance={},
                published_at=datetime.now(),
            )
        )
    return events


def test_cross_page_deterministic_ordering():
    all_events = generate_mock_events(100)
    reader = MockCanonicalEventReader(all_events)
    use_case = GetTimelineUseCase(reader)

    # Query page 1 (50 items)
    q1 = CanonicalEventQuery(series_id="s1", page=1, limit=50)
    res1 = use_case.execute(q1)

    # Query page 2 (50 items)
    q2 = CanonicalEventQuery(series_id="s1", page=2, limit=50)
    res2 = use_case.execute(q2)

    # Concat results
    combined = res1.items + res2.items

    # Should equal the internally sorted DB representation
    assert len(combined) == 100
    assert combined == reader.dtos

    # Verify duplicates
    ids = [item.id for item in combined]
    assert len(set(ids)) == 100
