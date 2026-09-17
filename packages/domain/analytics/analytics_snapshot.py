from dataclasses import dataclass

from .analytics_query import AnalyticsQuery
from .event_statistics import EventStatistics


@dataclass(frozen=True)
class AnalyticsSnapshot:
    """Recompute-all result of a scope. Pure derivation of canonical events —
    rebuilding it from the same store always yields identical values (M3.0.7)."""

    series_id: str
    from_chapter: int | None
    to_chapter: int | None
    statistics: EventStatistics

    @classmethod
    def for_query(
        cls, query: AnalyticsQuery, statistics: EventStatistics
    ) -> "AnalyticsSnapshot":
        return cls(
            series_id=query.series_id,
            from_chapter=query.from_chapter,
            to_chapter=query.to_chapter,
            statistics=statistics,
        )
