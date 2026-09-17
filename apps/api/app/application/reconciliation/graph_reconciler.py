import hashlib
from datetime import datetime

from apps.api.app.application.graph.graph_projection_service import (
    GraphProjectionService,
)
from packages.domain.canonical.reconciliation.projection_contract import (
    IssueType,
    ProjectionContract,
    ProjectionIntegrityChecker,
    ProjectionIssue,
    ProjectionRebuilder,
    ProjectionReport,
)


def deterministic_projection_key(event_id: str, rel_index: int) -> str:
    """Generates a deterministic key for a projected relationship."""
    raw = f"{event_id}:{rel_index}"
    return hashlib.sha256(raw.encode()).hexdigest()


class GraphIntegrityChecker(ProjectionIntegrityChecker):
    def __init__(self, repo):
        self.repo = repo

    def check_integrity(self, series_id: str) -> ProjectionReport:
        started = datetime.now()
        issues: list[ProjectionIssue] = []

        events = self.repo.get_all_events(series_id)
        relationships = self.repo.get_all_relationships(series_id)
        entities = self.repo.get_all_entities(series_id)

        # Build lookup sets
        event_ids: set[str] = {e["id"] for e in events}
        rel_event_ids: set[str] = {r["event_id"] for r in relationships}

        # 1. Missing Projections: events that SHOULD produce relationships but don't
        for event in events:
            if ProjectionContract.produces_graph_projection(event["type"]):
                if event.get("target_id") and event["id"] not in rel_event_ids:
                    issues.append(
                        ProjectionIssue(
                            type=IssueType.MISSING_RELATIONSHIP,
                            event_id=event["id"],
                            details=f"Event type {event['type']} with target_id should have projection",
                        )
                    )

        # 2. Orphan Relationships: relationships pointing to non-existent events
        for rel in relationships:
            if rel["event_id"] not in event_ids:
                issues.append(
                    ProjectionIssue(
                        type=IssueType.ORPHAN_RELATIONSHIP,
                        relationship_id=rel["id"],
                        event_id=rel["event_id"],
                        details="Relationship references non-existent event",
                    )
                )

        # 3. Duplicate Projections: same projection_key appearing more than once
        seen_keys: dict[str, str] = {}
        for i, rel in enumerate(relationships):
            key = deterministic_projection_key(
                rel["event_id"], rel.get("projection_index", 0)
            )
            if key in seen_keys:
                issues.append(
                    ProjectionIssue(
                        type=IssueType.DUPLICATE_PROJECTION,
                        relationship_id=rel["id"],
                        event_id=rel["event_id"],
                        details=f"Duplicate projection key with relationship {seen_keys[key]}",
                    )
                )
            seen_keys[key] = rel["id"]

        completed = datetime.now()

        return ProjectionReport(
            scan_started_at=started,
            scan_completed_at=completed,
            projection_version=ProjectionContract.GRAPH_PROJECTION_VERSION,
            total_events=len(events),
            total_entities=len(entities),
            total_relationships=len(relationships),
            issues=issues,
            repair_applied=False,
        )


class GraphRebuilder(ProjectionRebuilder):
    def __init__(self, repo, graph_projector: GraphProjectionService):
        self.repo = repo
        self.graph_projector = graph_projector
        self.checker = GraphIntegrityChecker(repo)

    def rebuild(self, series_id: str, dry_run: bool = True) -> ProjectionReport:
        # Step 1: Check current integrity
        pre_report = self.checker.check_integrity(series_id)

        if pre_report.is_consistent:
            return pre_report  # Nothing to fix

        if dry_run:
            return pre_report  # Report issues but don't mutate

        # Step 2: Atomic full rebuild inside single transaction
        def tx_action():
            # Clear existing graph projection
            self.repo.clear_graph_projection(series_id)

            # Replay all canonical events
            events = self.repo.get_all_events(series_id)
            for event in events:
                self.graph_projector.project_event(event, event["id"])

        self.repo.execute_rebuild_transaction(series_id, tx_action)

        # Step 3: Verify post-rebuild integrity
        post_report = self.checker.check_integrity(series_id)

        return ProjectionReport(
            scan_started_at=post_report.scan_started_at,
            scan_completed_at=post_report.scan_completed_at,
            projection_version=ProjectionContract.GRAPH_PROJECTION_VERSION,
            total_events=post_report.total_events,
            total_entities=post_report.total_entities,
            total_relationships=post_report.total_relationships,
            issues=post_report.issues,
            repair_applied=True,
        )
