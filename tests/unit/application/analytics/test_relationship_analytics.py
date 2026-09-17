"""M3.0.4 — Relationship analytics rules: pair normalization, delta grouping."""

import dataclasses

import pytest

from packages.domain.analytics.relationship_metric import RelationshipChapterDelta


class TestPairNormalization:
    def test_directional_pair_collapses(self):
        # A->B (3 events) and B->A (2 events) must merge into one pair bucket of 5.
        def normalize(a, b):
            lo, hi = (a, b) if a <= b else (b, a)
            return f"{lo}|{hi}"

        assert normalize("alice", "bob") == normalize("bob", "alice")
        counts = {normalize("alice", "bob"): 0}
        counts[normalize("bob", "alice")] = counts.get(normalize("alice", "bob"), 0) + 2
        counts[normalize("alice", "bob")] += 3
        assert len(counts) == 1
        assert list(counts.values())[0] == 5

    def test_self_pair_stable(self):
        a = "solo"
        lo, hi = sorted((a, a))
        assert lo == hi == a


class TestChapterDeltas:
    def test_delta_grouping_by_chapter(self):
        raw = {
            1: {"created": 2, "changed": 0, "ended": 0},
            3: {"created": 0, "changed": 1, "ended": 1},
            2: {"created": 1, "changed": 0, "ended": 0},
        }
        deltas = [
            RelationshipChapterDelta(chapter_number=ch, **raw[ch]) for ch in sorted(raw)
        ]
        assert [d.chapter_number for d in deltas] == [1, 2, 3]
        assert deltas[0].created == 2
        assert deltas[-1].ended == 1

    def test_delta_frozen(self):
        d = RelationshipChapterDelta(chapter_number=1, created=1, changed=0, ended=0)
        with pytest.raises(dataclasses.FrozenInstanceError):
            d.created = 5
