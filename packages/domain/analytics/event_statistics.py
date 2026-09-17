from dataclasses import dataclass

from .event_distribution_metric import EventDistributionMetric


@dataclass(frozen=True)
class EventStatistics:
    """M3.0.2 projection. All buckets are deterministic orderings of the
    scoped canonical event set; total_events is an independent COUNT,
    never a sum of buckets."""

    total_events: int
    chapters: int  # distinct chapters with >=1 event in scope
    events_by_chapter: tuple[EventDistributionMetric, ...]  # chapter ASC
    events_by_type: tuple[EventDistributionMetric, ...]  # count DESC, type ASC
    events_by_sequence: tuple[
        EventDistributionMetric, ...
    ]  # histogram of intra-chapter sequence values; sequence ASC
    events_by_entity: tuple[
        EventDistributionMetric, ...
    ]  # subject OR target; count DESC, entity ASC
