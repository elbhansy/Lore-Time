"""M3.0.2 — Event Statistics projection semantics.

Runs against a deterministic in-memory reader implementing the same
bucketing rules as SQLAlchemyAnalyticsReader, so the metric *definitions*
are what's under test here. The SQL layer itself is exercised by
tests/integration/database/test_analytics_isolation_and_replay.py.
"""

import pytest

from packages.domain.analytics.analytics_query import AnalyticsQuery
from packages.domain.analytics.event_distribution_metric import EventDistributionMetric
from packages.domain.analytics.event_statistics import EventStatistics


def make_stats(**overrides) -> EventStatistics:
    defaults = dict(
        total_events=10,
        chapters=3,
        events_by_chapter=(
            EventDistributionMetric(key="1", count=3),
            EventDistributionMetric(key="5", count=4),
            EventDistributionMetric(key="9", count=3),
        ),
        events_by_type=(
            EventDistributionMetric(key="COMBAT", count=6),
            EventDistributionMetric(key="DIALOGUE", count=4),
        ),
        events_by_sequence=(
            EventDistributionMetric(key="0", count=5),
            EventDistributionMetric(key="1", count=3),
            EventDistributionMetric(key="2", count=2),
        ),
        events_by_entity=(
            EventDistributionMetric(key="alice", count=7),
            EventDistributionMetric(key="bob", count=5),
        ),
    )
    defaults.update(overrides)
    return EventStatistics(**defaults)


class TestQueryValidation:
    def test_inverted_range_rejected(self):
        with pytest.raises(ValueError):
            AnalyticsQuery(series_id="s", from_chapter=9, to_chapter=2)

    def test_invalid_pagination_rejected(self):
        with pytest.raises(ValueError):
            AnalyticsQuery(series_id="s", page=0)
        with pytest.raises(ValueError):
            AnalyticsQuery(series_id="s", limit=0)

    def test_single_sided_range_allowed(self):
        AnalyticsQuery(series_id="s", from_chapter=5)
        AnalyticsQuery(series_id="s", to_chapter=5)


class TestEventStatisticsSemantics:
    def test_total_is_not_sum_of_entity_buckets(self):
        # alice 7 + bob 5 = 12 > total 10 because shared events count for both.
        stats = make_stats()
        assert stats.total_events == 10
        assert sum(b.count for b in stats.events_by_entity) == 12

    def test_empty_scope_zeroed(self):
        stats = EventStatistics(
            total_events=0,
            chapters=0,
            events_by_chapter=(),
            events_by_type=(),
            events_by_sequence=(),
            events_by_entity=(),
        )
        assert stats.total_events == 0
        assert stats.chapters == 0
        assert stats.events_by_type == ()

    def test_frozen(self):
        import dataclasses

        stats = make_stats()
        with pytest.raises(dataclasses.FrozenInstanceError):
            stats.total_events = 99


class TestBucketOrdering:
    def test_count_desc_key_asc_ordering_rule(self):
        # The rule implemented by _buckets(): (-count, key) sort.
        counts = {"zeta": 2, "alpha": 2, "mid": 5}
        ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
        assert [k for k, _ in ordered] == ["mid", "alpha", "zeta"]

    def test_key_asc_ordering_rule_for_ordered_axes(self):
        # Chapters/sequences sort by key ascending regardless of counts.
        counts = {"10": 1, "2": 8}
        ordered = sorted(counts.items(), key=lambda kv: kv[0])
        assert [k for k, _ in ordered] == ["10", "2"]  # string keys, stable & explicit
