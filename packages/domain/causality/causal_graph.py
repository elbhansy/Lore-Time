"""Directed Causal Graph (Phase 5.2 Milestone 5.2.5).

Represents a deterministic directed graph of causal relations with adjacency lookups,
cycle detection, and explicit canonical ordering.
"""

from packages.domain.causality.models import (
    CausalConflict,
    CausalConflictStatus,
    CausalRelation,
    CausalRelationType,
)


class CausalGraph:
    """Deterministic directed graph of causal relations."""

    def __init__(self, series_id: str, reader_chapter: int | None = None):
        self.series_id = series_id
        self.reader_chapter = reader_chapter
        self._relations: dict[str, CausalRelation] = {}
        self._outgoing: dict[
            str, list[str]
        ] = {}  # source_event_id -> [relation_id, ...]
        self._incoming: dict[
            str, list[str]
        ] = {}  # target_event_id -> [relation_id, ...]
        self._nodes: set[str] = set()

    def add_relation(self, relation: CausalRelation) -> None:
        """Adds a relation and updates adjacency indices."""
        self._relations[relation.relation_id] = relation
        self._nodes.add(relation.source_event_id)
        self._nodes.add(relation.target_event_id)

        if relation.relation_id not in self._outgoing.setdefault(
            relation.source_event_id, []
        ):
            self._outgoing[relation.source_event_id].append(relation.relation_id)

        if relation.relation_id not in self._incoming.setdefault(
            relation.target_event_id, []
        ):
            self._incoming[relation.target_event_id].append(relation.relation_id)

    def contains(self, relation_id: str) -> bool:
        return relation_id in self._relations

    def get_relation(self, relation_id: str) -> CausalRelation | None:
        return self._relations.get(relation_id)

    def get_outgoing_relations(self, event_id: str) -> list[CausalRelation]:
        """Returns outgoing relations from an event, deterministically ordered."""
        r_ids = self._outgoing.get(event_id, [])
        rels = [self._relations[rid] for rid in r_ids]
        return sorted(
            rels,
            key=lambda r: (
                r.target_chapter,
                r.target_event_id,
                r.relation_type.value,
                r.relation_id,
            ),
        )

    def get_incoming_relations(self, event_id: str) -> list[CausalRelation]:
        """Returns incoming relations leading to an event, deterministically ordered."""
        r_ids = self._incoming.get(event_id, [])
        rels = [self._relations[rid] for rid in r_ids]
        return sorted(
            rels,
            key=lambda r: (
                r.source_chapter,
                r.source_event_id,
                r.relation_type.value,
                r.relation_id,
            ),
        )

    def get_all_relations(self) -> list[CausalRelation]:
        """Returns all relations in deterministic order."""
        return sorted(
            list(self._relations.values()),
            key=lambda r: (
                r.source_chapter,
                r.target_chapter,
                r.source_event_id,
                r.target_event_id,
                r.relation_type.value,
                r.relation_id,
            ),
        )

    def detect_cycles(self) -> list[list[str]]:
        """Detects any directed cycles in the causal graph using deterministic DFS.

        Returns list of cycles (each cycle is a list of event_ids in visit order).
        """
        visited: set[str] = set()
        rec_stack: list[str] = []
        cycles: list[list[str]] = []

        # Sort nodes deterministically for reproducible cycle discovery
        all_nodes = sorted(list(self._nodes))

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.append(node)

            for rel in self.get_outgoing_relations(node):
                target = rel.target_event_id
                if target not in visited:
                    dfs(target)
                elif target in rec_stack:
                    # Found cycle!
                    cycle_start_idx = rec_stack.index(target)
                    cycles.append(list(rec_stack[cycle_start_idx:]))

            rec_stack.pop()

        for node in all_nodes:
            if node not in visited:
                dfs(node)

        return cycles

    def find_contradictions(self) -> list[CausalConflict]:
        """Finds contradictory or conflicting causal relations leading into the same target event."""
        conflicts: list[CausalConflict] = []

        # Group incoming relations by target_event_id
        for target_id in sorted(list(self._incoming.keys())):
            incoming_rels = self.get_incoming_relations(target_id)
            if len(incoming_rels) > 1:
                # Check for mutually exclusive causes (e.g. multiple distinct death causes)
                direct_causes = [
                    r
                    for r in incoming_rels
                    if r.relation_type == CausalRelationType.DIRECT_CAUSE
                    or r.relation_type == CausalRelationType.STATE_TRANSITION
                ]

                if len(direct_causes) > 1:
                    conflicts.append(
                        CausalConflict(
                            conflict_id=f"conflict:{self.series_id}:{target_id}",
                            series_id=self.series_id,
                            target_event_id=target_id,
                            conflicting_relation_ids=tuple(
                                r.relation_id for r in direct_causes
                            ),
                            conflict_type="MUTUALLY_EXCLUSIVE_DIRECT_CAUSES",
                            evidence_summary=f"Target event {target_id} has {len(direct_causes)} direct causes.",
                            resolution_status=CausalConflictStatus.UNRESOLVED,
                        )
                    )

        return conflicts
