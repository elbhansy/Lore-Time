from apps.api.app.application.graph.graph_projection_service import (
    GraphProjectionService,
)
from apps.api.app.application.reconciliation.graph_reconciler import (
    GraphIntegrityChecker,
    GraphRebuilder,
)
from packages.domain.canonical.reconciliation.projection_contract import IssueType


class MockReconciliationRepo:
    def __init__(self):
        self.events = []
        self.relationships = []
        self.entities = {}
        self.rebuild_tx_count = 0

    def get_all_events(self, series_id):
        return [e for e in self.events if e["series_id"] == series_id]

    def get_all_relationships(self, series_id):
        return [r for r in self.relationships if r["series_id"] == series_id]

    def get_all_entities(self, series_id):
        return {k: v for k, v in self.entities.items() if v["series_id"] == series_id}

    def clear_graph_projection(self, series_id):
        self.relationships = [
            r for r in self.relationships if r["series_id"] != series_id
        ]
        self.entities = {
            k: v for k, v in self.entities.items() if v["series_id"] != series_id
        }

    def execute_rebuild_transaction(self, series_id, action):
        # Simulate atomic transaction with rollback
        backup_rels = list(self.relationships)
        backup_ents = dict(self.entities)
        try:
            action()
        except Exception:
            self.relationships = backup_rels
            self.entities = backup_ents
            raise
        self.rebuild_tx_count += 1

    # GraphProjectionService calls these
    def ensure_entity_exists(self, entity_id, series_id, type, name):
        key = f"{series_id}:{entity_id}"
        if key not in self.entities:
            self.entities[key] = {
                "id": entity_id,
                "series_id": series_id,
                "type": type,
                "name": name,
            }

    def create_relationship(
        self, series_id, source_id, target_id, rel_type, event_id, sequence
    ):
        self.relationships.append(
            {
                "id": f"rel_{len(self.relationships)}",
                "series_id": series_id,
                "source_id": source_id,
                "target_id": target_id,
                "type": rel_type,
                "event_id": event_id,
                "sequence": sequence,
                "projection_index": 0,
            }
        )


# ====== TESTS ======


def test_empty_relationship_event_no_false_positive():
    """Event types that don't produce graph projections should NOT trigger MISSING_RELATIONSHIP."""
    repo = MockReconciliationRepo()
    checker = GraphIntegrityChecker(repo)

    # DIALOGUE event — not in ProjectionContract.GRAPH_PRODUCING_TYPES
    repo.events.append(
        {
            "id": "evt_1",
            "series_id": "s1",
            "type": "DIALOGUE",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {},
        }
    )

    report = checker.check_integrity("s1")
    assert report.is_consistent
    assert report.issues_count == 0


def test_missing_projection_detection():
    """Event that SHOULD produce a relationship but doesn't → MISSING_RELATIONSHIP."""
    repo = MockReconciliationRepo()
    checker = GraphIntegrityChecker(repo)

    # RELATIONSHIP_CHANGED event with target_id but no relationship projected
    repo.events.append(
        {
            "id": "evt_2",
            "series_id": "s1",
            "type": "RELATIONSHIP_CHANGED",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {},
        }
    )

    report = checker.check_integrity("s1")
    assert not report.is_consistent
    assert report.issues_count == 1
    assert report.issues[0].type == IssueType.MISSING_RELATIONSHIP


def test_orphan_relationship_detection():
    """Relationship pointing to a non-existent event → ORPHAN_RELATIONSHIP."""
    repo = MockReconciliationRepo()
    checker = GraphIntegrityChecker(repo)

    # No events exist, but a relationship does
    repo.relationships.append(
        {
            "id": "rel_orphan",
            "series_id": "s1",
            "source_id": "alice",
            "target_id": "bob",
            "type": "KNOWS",
            "event_id": "nonexistent_event",
            "sequence": 0,
            "projection_index": 0,
        }
    )

    report = checker.check_integrity("s1")
    assert not report.is_consistent
    assert report.issues_count == 1
    assert report.issues[0].type == IssueType.ORPHAN_RELATIONSHIP


def test_dry_run_zero_mutations():
    """reconcile(dry_run=True) must report issues but never mutate the database."""
    repo = MockReconciliationRepo()
    projector = GraphProjectionService(repo)
    rebuilder = GraphRebuilder(repo, projector)

    # Create an event that should have a projection but doesn't
    repo.events.append(
        {
            "id": "evt_3",
            "series_id": "s1",
            "type": "RELATIONSHIP_CHANGED",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {},
        }
    )

    report = rebuilder.rebuild("s1", dry_run=True)

    # Should report the issue
    assert report.issues_count == 1
    # Should NOT have mutated anything
    assert report.repair_applied == False
    assert len(repo.relationships) == 0
    assert repo.rebuild_tx_count == 0


def test_full_rebuild_restores_graph():
    """Delete all projections, rebuild from canonical events, and verify graph is restored."""
    repo = MockReconciliationRepo()
    projector = GraphProjectionService(repo)
    rebuilder = GraphRebuilder(repo, projector)

    # Add a graph-producing event
    repo.events.append(
        {
            "id": "evt_4",
            "series_id": "s1",
            "type": "RELATIONSHIP_CHANGED",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {},
        }
    )

    # Run actual rebuild
    report = rebuilder.rebuild("s1", dry_run=False)

    assert report.repair_applied == True
    assert len(repo.relationships) == 1
    assert repo.relationships[0]["source_id"] == "alice"
    assert repo.relationships[0]["target_id"] == "bob"


def test_idempotent_replay():
    """Replaying 3 times must produce byte-identical graph state each time."""
    repo = MockReconciliationRepo()
    projector = GraphProjectionService(repo)
    rebuilder = GraphRebuilder(repo, projector)

    # Two graph-producing events
    repo.events = [
        {
            "id": "evt_a",
            "series_id": "s1",
            "type": "COMBAT",
            "subject_id": "alice",
            "target_id": "dragon",
            "metadata": {},
        },
        {
            "id": "evt_b",
            "series_id": "s1",
            "type": "ALLIANCE_FORMED",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {},
        },
    ]

    # Rebuild 3 times
    snapshots = []
    for _ in range(3):
        rebuilder.rebuild("s1", dry_run=False)
        snapshot = {
            "entities": sorted(repo.entities.keys()),
            "rel_count": len(repo.relationships),
            "rel_sources": [
                (r["source_id"], r["target_id"], r["type"]) for r in repo.relationships
            ],
        }
        snapshots.append(snapshot)

    # All 3 must be identical
    assert snapshots[0] == snapshots[1]
    assert snapshots[1] == snapshots[2]


def test_canonical_event_immutability():
    """Reconciliation must NEVER alter canonical events."""
    repo = MockReconciliationRepo()
    projector = GraphProjectionService(repo)
    rebuilder = GraphRebuilder(repo, projector)

    original_events = [
        {
            "id": "evt_x",
            "series_id": "s1",
            "type": "RELATIONSHIP_CHANGED",
            "subject_id": "alice",
            "target_id": "bob",
            "metadata": {"original": True},
        }
    ]
    repo.events = list(original_events)  # Copy

    events_before = [dict(e) for e in repo.events]

    rebuilder.rebuild("s1", dry_run=False)

    events_after = [dict(e) for e in repo.events]

    assert events_before == events_after
