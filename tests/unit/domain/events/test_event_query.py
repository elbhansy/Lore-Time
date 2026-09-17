import pytest

from packages.domain.events.event_query import EventQuery
from packages.domain.services.event_query_service import EventQueryService


class MockEventRepo:
    def query(self, q: EventQuery):
        # Mocks deterministic postgres ordering and visibility filtering
        all_events = [
            {"id": "e1", "chap": 40, "seq": 1},
            {"id": "e2", "chap": 60, "seq": 1},
            {"id": "e3", "chap": 90, "seq": 1},
            {"id": "e4", "chap": 120, "seq": 1},
            {"id": "e5", "chap": 200, "seq": 1},
        ]

        filtered = [
            e
            for e in all_events
            if e["chap"] >= q.from_chapter and e["chap"] <= q.to_chapter
        ]

        offset = (q.page - 1) * q.page_size
        return filtered[offset : offset + q.page_size]

    def count(self, q: EventQuery):
        all_events = [
            {"id": "e1", "chap": 40, "seq": 1},
            {"id": "e2", "chap": 60, "seq": 1},
            {"id": "e3", "chap": 90, "seq": 1},
            {"id": "e4", "chap": 120, "seq": 1},
            {"id": "e5", "chap": 200, "seq": 1},
        ]

        filtered = [
            e
            for e in all_events
            if e["chap"] >= q.from_chapter and e["chap"] <= q.to_chapter
        ]
        return len(filtered)


def test_event_query_validation():
    # Range leak test
    with pytest.raises(ValueError, match="to_chapter cannot exceed reader_chapter"):
        EventQuery(series_id="s1", reader_chapter=100, from_chapter=1, to_chapter=200)

    with pytest.raises(ValueError, match="from_chapter must be <= to_chapter"):
        EventQuery(series_id="s1", reader_chapter=100, from_chapter=50, to_chapter=20)


def test_event_query_service_success():
    repo = MockEventRepo()
    service = EventQueryService(repo)

    q = EventQuery(series_id="s1", reader_chapter=100, from_chapter=1, to_chapter=100)

    res = service.query(q)

    assert res.total == 3
    assert len(res.items) == 3

    ids = [e["id"] for e in res.items]
    assert "e1" in ids
    assert "e2" in ids
    assert "e3" in ids
    assert "e4" not in ids
    assert "e5" not in ids
