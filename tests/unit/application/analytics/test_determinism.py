"""M3.0.7 — Determinism invariant: same canonical dataset, N runs,
byte-identical snapshot (asdict comparison). Uses a stub AnalyticsReader
that mirrors the reader's ordering rules over a fixed in-memory dataset.
"""

import dataclasses

from packages.domain.analytics.analytics_query import AnalyticsQuery
from packages.domain.analytics.analytics_reader import AnalyticsReader
from packages.domain.analytics.character_activity_metric import CharacterActivityMetric
from packages.domain.analytics.event_distribution_metric import EventDistributionMetric
from packages.domain.analytics.event_statistics import EventStatistics
from packages.domain.analytics.relationship_metric import (
    RelationshipAnalytics,
    RelationshipChapterDelta,
)

# Canonical dataset: (chapter, sequence, type, subject, target)
DATASET = [
    (1, 0, "RELATIONSHIP_CREATED", "alice", "bob"),
    (1, 1, "DIALOGUE", "alice", "bob"),
    (2, 0, "COMBAT", "bob", "carol"),
    (2, 1, "COMBAT", "carol", None),
    (3, 0, "RELATIONSHIP_ENDED", "alice", "bob"),
    (3, 1, "DIALOGUE", "carol", "bob"),
    (3, 2, "COMBAT", "alice", "carol"),
]


class StubAnalyticsReader(AnalyticsReader):
    """Pure-Python mirror of the SQL reader's derivation rules."""

    def _scoped(self, q):
        return [
            e
            for e in DATASET
            if (q.from_chapter is None or e[0] >= q.from_chapter)
            and (q.to_chapter is None or e[0] <= q.to_chapter)
        ]

    def get_event_statistics(self, q) -> EventStatistics:
        rows = self._scoped(q)
        by_chapter, by_type, by_seq = {}, {}, {}
        by_entity = {}
        for ch, seq, typ, subj, tgt in rows:
            by_chapter[str(ch)] = by_chapter.get(str(ch), 0) + 1
            by_type[typ] = by_type.get(typ, 0) + 1
            by_seq[str(seq)] = by_seq.get(str(seq), 0) + 1
            by_entity[subj] = by_entity.get(subj, 0) + 1
            if tgt:
                by_entity[tgt] = by_entity.get(tgt, 0) + 1
        buckets = lambda d, key_asc=False: tuple(
            EventDistributionMetric(key=k, count=v)
            for k, v in sorted(
                d.items(), key=lambda kv: kv[0] if key_asc else (-kv[1], kv[0])
            )
        )
        return EventStatistics(
            total_events=len(rows),
            chapters=len(by_chapter),
            events_by_chapter=buckets(by_chapter, key_asc=True),
            events_by_type=buckets(by_type),
            events_by_sequence=buckets(by_seq, key_asc=True),
            events_by_entity=buckets(by_entity),
        )

    def get_entity_activity(self, q, entity_id=None):
        rows = self._scoped(q)
        entities = sorted({e[3] for e in rows} | {e[4] for e in rows if e[4]})
        out = []
        for eid in entities:
            if entity_id and eid != entity_id:
                continue
            mine = [e for e in rows if e[3] == eid or e[4] == eid]
            subj = sum(1 for e in mine if e[3] == eid)
            tgt = sum(1 for e in mine if e[4] == eid)
            chapters = sorted({e[0] for e in mine})
            out.append(
                CharacterActivityMetric(
                    entity_id=eid,
                    event_count=len(mine),
                    subject_count=subj,
                    target_count=tgt,
                    relationship_count=0,
                    chapters_present=len(chapters),
                    first_seen_chapter=chapters[0] if chapters else None,
                    last_seen_chapter=chapters[-1] if chapters else None,
                )
            )
        return sorted(out, key=lambda m: (-m.event_count, m.entity_id))

    def get_relationship_analytics(self, q) -> RelationshipAnalytics:
        rows = self._scoped(q)
        deltas = {}
        for ch, seq, typ, subj, tgt in rows:
            kind = {
                "RELATIONSHIP_CREATED": "created",
                "RELATIONSHIP_CHANGED": "changed",
                "RELATIONSHIP_ENDED": "ended",
            }.get(typ)
            if kind:
                d = deltas.setdefault(ch, {"created": 0, "changed": 0, "ended": 0})
                d[kind] += 1
        return RelationshipAnalytics(
            frequency=(),
            most_connected=(),
            interaction_frequency=(),
            changes_by_chapter=tuple(
                RelationshipChapterDelta(chapter_number=ch, **deltas[ch])
                for ch in sorted(deltas)
            ),
        )


def test_three_runs_byte_identical():
    q = AnalyticsQuery(series_id="s")
    snapshots = [StubAnalyticsReader().rebuild(q) for _ in range(3)]
    as_dicts = [dataclasses.asdict(s) for s in snapshots]
    assert as_dicts[0] == as_dicts[1] == as_dicts[2]


def test_rebuild_is_scope_stable():
    reader = StubAnalyticsReader()
    full = dataclasses.asdict(reader.rebuild(AnalyticsQuery(series_id="s")))
    again = dataclasses.asdict(reader.rebuild(AnalyticsQuery(series_id="s")))
    assert full == again


def test_scoped_run_matches_manual_count():
    reader = StubAnalyticsReader()
    stats = reader.get_event_statistics(
        AnalyticsQuery(series_id="s", from_chapter=2, to_chapter=3)
    )
    manual = [e for e in DATASET if 2 <= e[0] <= 3]
    assert stats.total_events == len(manual)


def test_replay_after_reset_identical():
    """Replayability: simulate projection deletion + rebuild."""
    import copy

    reader = StubAnalyticsReader()
    first = copy.deepcopy(
        dataclasses.asdict(reader.rebuild(AnalyticsQuery(series_id="s")))
    )
    del reader  # 'drop the projection'
    second = dataclasses.asdict(
        StubAnalyticsReader().rebuild(AnalyticsQuery(series_id="s"))
    )
    assert first == second
