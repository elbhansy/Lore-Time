from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from infrastructure.database.models.canonical_entity import CanonicalEntityModel
from infrastructure.database.models.canonical_relationship import (
    CanonicalRelationshipModel,
)
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from packages.domain.analytics.analytics_query import AnalyticsQuery
from packages.domain.analytics.analytics_reader import AnalyticsReader
from packages.domain.analytics.character_activity_metric import CharacterActivityMetric
from packages.domain.analytics.event_distribution_metric import EventDistributionMetric
from packages.domain.analytics.event_statistics import EventStatistics
from packages.domain.analytics.relationship_metric import (
    RelationshipAnalytics,
    RelationshipChapterDelta,
    RelationshipMetric,
)


def _buckets(
    counts: dict[str, int], *, by_key_asc: bool = False
) -> tuple[EventDistributionMetric, ...]:
    """Deterministic bucket ordering (R3): count DESC, key ASC — or key ASC when
    the axis is inherently ordered (chapter numbers, sequence positions)."""
    ordered = sorted(
        counts.items(), key=lambda kv: kv[0] if by_key_asc else (-kv[1], kv[0])
    )
    return tuple(EventDistributionMetric(key=k, count=v) for k, v in ordered)


class SQLAlchemyAnalyticsReader(AnalyticsReader):
    """Read-only analytics over canonical tables. Never mutates (R1)."""

    def __init__(self, session: Session):
        self.session = session

    # ------------------------------------------------------------------
    # Shared scoped-event subquery. All chapter scoping goes through the
    # ChapterModel join (same as SQLAlchemyCanonicalEventReader).
    # ------------------------------------------------------------------
    def _scoped_event_subquery(self, query: AnalyticsQuery):
        stmt = (
            select(
                EventModel.type.label("type"),
                EventModel.subject_id.label("subject_id"),
                EventModel.target_id.label("target_id"),
                EventModel.sequence.label("sequence"),
                ChapterModel.number.label("chapter_number"),
            )
            .join(ChapterModel, EventModel.chapter_id == ChapterModel.id)
            .where(EventModel.series_id == query.series_id)
        )
        if query.from_chapter is not None:
            stmt = stmt.where(ChapterModel.number >= query.from_chapter)
        if query.to_chapter is not None:
            stmt = stmt.where(ChapterModel.number <= query.to_chapter)
        return stmt.subquery()

    def _series_exists(self, series_id: str) -> bool:
        from infrastructure.database.models.series import SeriesModel

        stmt = (
            select(func.count())
            .select_from(SeriesModel)
            .where(SeriesModel.id == series_id)
        )
        return bool(self.session.execute(stmt).scalar())

    # ------------------------------------------------------------------
    # M3.0.2 — Event Statistics
    # ------------------------------------------------------------------
    def get_event_statistics(self, query: AnalyticsQuery) -> EventStatistics:
        base = self._scoped_event_subquery(query)

        total_events = (
            self.session.execute(select(func.count()).select_from(base)).scalar() or 0
        )

        distinct_chapters = (
            self.session.execute(
                select(func.count(func.distinct(base.c.chapter_number))).select_from(
                    base
                )
            ).scalar()
            or 0
        )

        events_by_chapter: dict[str, int] = {}
        for row in self.session.execute(
            select(base.c.chapter_number, func.count())
            .select_from(base)
            .group_by(base.c.chapter_number)
        ):
            events_by_chapter[str(row[0])] = row[1]

        events_by_type: dict[str, int] = {}
        for row in self.session.execute(
            select(base.c.type, func.count()).select_from(base).group_by(base.c.type)
        ):
            events_by_type[row[0]] = row[1]

        # Q1 decision: histogram of intra-chapter sequence positions.
        events_by_sequence: dict[str, int] = {}
        for row in self.session.execute(
            select(base.c.sequence, func.count())
            .select_from(base)
            .group_by(base.c.sequence)
        ):
            events_by_sequence[str(row[0])] = row[1]

        # Entity side union; NULL targets counted once, under the subject only.
        events_by_entity: dict[str, int] = defaultdict(int)
        for row in self.session.execute(
            select(base.c.subject_id, func.count())
            .select_from(base)
            .group_by(base.c.subject_id)
        ):
            events_by_entity[str(row[0])] += row[1]
        for row in self.session.execute(
            select(base.c.target_id, func.count())
            .select_from(base)
            .where(base.c.target_id.isnot(None))
            .group_by(base.c.target_id)
        ):
            events_by_entity[str(row[0])] += row[1]

        return EventStatistics(
            total_events=total_events,
            chapters=distinct_chapters,
            events_by_chapter=_buckets(events_by_chapter, by_key_asc=True),
            events_by_type=_buckets(events_by_type),
            events_by_sequence=_buckets(events_by_sequence, by_key_asc=True),
            events_by_entity=_buckets(dict(events_by_entity)),
        )

    # ------------------------------------------------------------------
    # M3.0.3 — Entity Activity
    # ------------------------------------------------------------------
    def get_entity_activity(
        self,
        query: AnalyticsQuery,
        entity_id: str | None = None,
    ) -> list[CharacterActivityMetric]:
        base = self._scoped_event_subquery(query)

        # Per-entity combined stats over both sides in one pass (UNION ALL),
        # plus per-side counts separately.
        both_sides = (
            select(
                base.c.subject_id.label("eid"),
                base.c.chapter_number.label("chapter_number"),
            )
            .union_all(
                select(
                    base.c.target_id.label("eid"),
                    base.c.chapter_number.label("chapter_number"),
                ).where(base.c.target_id.isnot(None))
            )
            .subquery()
        )

        combined = {
            str(row[0]): row[1:]
            for row in self.session.execute(
                select(
                    both_sides.c.eid,
                    func.count().label("event_count"),
                    func.count(func.distinct(both_sides.c.chapter_number)).label(
                        "chapters_present"
                    ),
                    func.min(both_sides.c.chapter_number).label("first_seen"),
                    func.max(both_sides.c.chapter_number).label("last_seen"),
                ).group_by(both_sides.c.eid)
            )
        }

        subject_counts = {
            str(row[0]): row[1]
            for row in self.session.execute(
                select(base.c.subject_id, func.count())
                .select_from(base)
                .group_by(base.c.subject_id)
            )
        }
        target_counts = {
            str(row[0]): row[1]
            for row in self.session.execute(
                select(base.c.target_id, func.count())
                .select_from(base)
                .where(base.c.target_id.isnot(None))
                .group_by(base.c.target_id)
            )
        }

        # Canonical entity universe for the series (reuses the canonical
        # projection — zero-event entities still appear, honest empties).
        entity_stmt = select(CanonicalEntityModel.id).where(
            CanonicalEntityModel.series_id == query.series_id
        )
        if entity_id is not None:
            entity_stmt = entity_stmt.where(CanonicalEntityModel.id == entity_id)
        universe = [str(row[0]) for row in self.session.execute(entity_stmt)]

        rel_counts = self._relationship_counts_by_entity(query)

        metrics: list[CharacterActivityMetric] = []
        for eid in universe:
            if eid in combined:
                event_count, chapters_present, first_seen, last_seen = combined[eid]
            else:
                event_count, chapters_present, first_seen, last_seen = 0, 0, None, None
            metrics.append(
                CharacterActivityMetric(
                    entity_id=eid,
                    event_count=event_count,
                    subject_count=subject_counts.get(eid, 0),
                    target_count=target_counts.get(eid, 0),
                    relationship_count=rel_counts.get(eid, 0),
                    chapters_present=chapters_present,
                    first_seen_chapter=first_seen,
                    last_seen_chapter=last_seen,
                )
            )

        # R3: event_count DESC, entity_id ASC.
        metrics.sort(key=lambda m: (-m.event_count, m.entity_id))
        return metrics

    def _relationship_counts_by_entity(self, query: AnalyticsQuery) -> dict[str, int]:
        """Rows in the canonical relationship projection touching an entity
        on either side, scoped by series + chapter range (via the owning
        event's chapter)."""
        rel_base = self._scoped_relationship_subquery(query)
        counts: dict[str, int] = defaultdict(int)
        for row in self.session.execute(
            select(rel_base.c.source_entity_id, func.count())
            .select_from(rel_base)
            .group_by(rel_base.c.source_entity_id)
        ):
            counts[str(row[0])] += row[1]
        for row in self.session.execute(
            select(rel_base.c.target_entity_id, func.count())
            .select_from(rel_base)
            .group_by(rel_base.c.target_entity_id)
        ):
            counts[str(row[0])] += row[1]
        return dict(counts)

    def _scoped_relationship_subquery(self, query: AnalyticsQuery):
        """Canonical relationships joined to their chapter for range scoping."""
        stmt = (
            select(
                CanonicalRelationshipModel.id.label("rel_id"),
                CanonicalRelationshipModel.source_entity_id.label("source_entity_id"),
                CanonicalRelationshipModel.target_entity_id.label("target_entity_id"),
                CanonicalRelationshipModel.type.label("rel_type"),
            )
            .join(EventModel, CanonicalRelationshipModel.event_id == EventModel.id)
            .join(ChapterModel, EventModel.chapter_id == ChapterModel.id)
            .where(CanonicalRelationshipModel.series_id == query.series_id)
        )
        if query.from_chapter is not None:
            stmt = stmt.where(ChapterModel.number >= query.from_chapter)
        if query.to_chapter is not None:
            stmt = stmt.where(ChapterModel.number <= query.to_chapter)
        return stmt.subquery()

    # ------------------------------------------------------------------
    # M3.0.4 — Relationship Analytics
    # ------------------------------------------------------------------
    def get_relationship_analytics(
        self, query: AnalyticsQuery
    ) -> RelationshipAnalytics:
        rel_base = self._scoped_relationship_subquery(query)

        # Directional frequency per (source entity, type).
        frequency_map: dict[tuple[str, str], int] = defaultdict(int)
        for row in self.session.execute(
            select(rel_base.c.source_entity_id, rel_base.c.rel_type, func.count())
            .select_from(rel_base)
            .group_by(rel_base.c.source_entity_id, rel_base.c.rel_type)
        ):
            frequency_map[(str(row[0]), row[1])] = row[2]
        frequency = tuple(
            RelationshipMetric(entity_id=eid, relationship_type=rtype, count=count)
            for (eid, rtype), count in sorted(
                frequency_map.items(), key=lambda kv: (-kv[1], kv[0][1], kv[0][0])
            )  # count DESC, type ASC, entity ASC
        )

        # Most connected: distinct counterpart count per entity (either side).
        directed = (
            select(
                rel_base.c.source_entity_id.label("eid"),
                rel_base.c.target_entity_id.label("counterpart"),
            )
            .union_all(
                select(
                    rel_base.c.target_entity_id.label("eid"),
                    rel_base.c.source_entity_id.label("counterpart"),
                )
            )
            .subquery()
        )
        most_connected_map: dict[str, int] = {}
        for row in self.session.execute(
            select(directed.c.eid, func.count(func.distinct(directed.c.counterpart)))
            .select_from(directed)
            .group_by(directed.c.eid)
        ):
            most_connected_map[str(row[0])] = row[1]

        # Pair interactions from canonical events (subject->target),
        # normalized so A->B and B->A collapse into one bucket.
        ev_base = self._scoped_event_subquery(query)
        pair_map: dict[str, int] = defaultdict(int)
        for row in self.session.execute(
            select(ev_base.c.subject_id, ev_base.c.target_id, func.count())
            .select_from(ev_base)
            .where(ev_base.c.target_id.isnot(None))
            .group_by(ev_base.c.subject_id, ev_base.c.target_id)
        ):
            a, b = str(row[0]), str(row[1])
            lo, hi = (a, b) if a <= b else (b, a)
            pair_map[f"{lo}|{hi}"] += row[2]

        # Chapter-by-chapter deltas from RELATIONSHIP_* events.
        delta_types = {
            "RELATIONSHIP_CREATED": "created",
            "RELATIONSHIP_CHANGED": "changed",
            "RELATIONSHIP_ENDED": "ended",
        }
        deltas_raw: dict[int, dict[str, int]] = defaultdict(
            lambda: {"created": 0, "changed": 0, "ended": 0}
        )
        for row in self.session.execute(
            select(ev_base.c.type, ev_base.c.chapter_number, func.count())
            .select_from(ev_base)
            .where(ev_base.c.type.in_(delta_types.keys()))
            .group_by(ev_base.c.type, ev_base.c.chapter_number)
        ):
            deltas_raw[row[1]][delta_types[row[0]]] = row[2]

        return RelationshipAnalytics(
            frequency=frequency,
            most_connected=_buckets(most_connected_map),
            interaction_frequency=_buckets(dict(pair_map)),
            changes_by_chapter=tuple(
                RelationshipChapterDelta(chapter_number=ch, **deltas_raw[ch])
                for ch in sorted(deltas_raw)
            ),
        )
