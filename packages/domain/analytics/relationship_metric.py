from dataclasses import dataclass

from .event_distribution_metric import EventDistributionMetric


@dataclass(frozen=True)
class RelationshipMetric:
    """Per (entity, relationship type) frequency — one row of the
    'Alice: KNOWS 14 / ATTACKED 7' view. Directional: counts the
    canonical relationship rows where this entity is the source."""

    entity_id: str
    relationship_type: str
    count: int


@dataclass(frozen=True)
class RelationshipChapterDelta:
    """Chapter-by-chapter relationship change counts, derived from
    RELATIONSHIP_* canonical events."""

    chapter_number: int
    created: int
    changed: int
    ended: int


@dataclass(frozen=True)
class RelationshipAnalytics:
    frequency: tuple[RelationshipMetric, ...]  # count DESC, type ASC, entity ASC
    most_connected: tuple[EventDistributionMetric, ...]  # degree DESC, entity ASC
    interaction_frequency: tuple[
        EventDistributionMetric, ...
    ]  # pair buckets, count DESC, key ASC
    changes_by_chapter: tuple[RelationshipChapterDelta, ...]  # chapter ASC
