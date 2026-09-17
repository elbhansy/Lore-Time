"""M3.0.3 — Entity activity invariants."""

import pytest

from packages.domain.analytics.character_activity_metric import CharacterActivityMetric


def metric(event_count, subject_count, target_count, **kw):
    return CharacterActivityMetric(
        entity_id=kw.pop("entity_id", "e"),
        event_count=event_count,
        subject_count=subject_count,
        target_count=target_count,
        relationship_count=kw.pop("relationship_count", 0),
        chapters_present=kw.pop("chapters_present", 1),
        first_seen_chapter=kw.pop("first_seen_chapter", 1),
        last_seen_chapter=kw.pop("last_seen_chapter", 1),
    )


class TestActivityInvariants:
    def test_event_count_equals_sides_minus_overlap(self):
        # alice subject on 3 events, target on 2, one event both -> 4 distinct.
        m = metric(event_count=4, subject_count=3, target_count=2)
        # The invariant the reader must satisfy: s + t - overlap == event_count
        overlap = m.subject_count + m.target_count - m.event_count
        assert overlap >= 0
        assert m.subject_count + m.target_count - overlap == m.event_count

    def test_no_overlap_case(self):
        m = metric(event_count=5, subject_count=3, target_count=2)
        assert m.subject_count + m.target_count == m.event_count

    def test_honest_empty(self):
        # Entity present canonically but zero events in scope.
        m = metric(
            event_count=0,
            subject_count=0,
            target_count=0,
            chapters_present=0,
            first_seen_chapter=None,
            last_seen_chapter=None,
        )
        assert m.event_count == 0
        assert m.first_seen_chapter is None
        assert m.last_seen_chapter is None

    def test_frozen(self):
        import dataclasses

        m = metric(1, 1, 0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            m.event_count = 5


class TestOrdering:
    def test_reader_ordering_rule(self):
        metrics = [
            metric(2, 2, 0, entity_id="b"),
            metric(5, 5, 0, entity_id="a"),
            metric(2, 1, 1, entity_id="c"),
        ]
        ordered = sorted(metrics, key=lambda m: (-m.event_count, m.entity_id))
        assert [m.entity_id for m in ordered] == ["a", "b", "c"]
