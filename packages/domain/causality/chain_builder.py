"""Multi-Hop Causal Chain Builder (Phase 5.2 Milestones 5.2.6 & 5.2.7).

Traverses the CausalGraph to extract upstream causal chains and downstream effect chains
with depth boundaries, cycle protection, and indirect influence derivation.
"""

from packages.domain.causality.causal_graph import CausalGraph
from packages.domain.causality.impact_scorer import compute_causal_impact_score
from packages.domain.causality.models import (
    CausalChain,
    CausalConfidence,
    CausalDerivationType,
    CausalEvidenceReference,
    CausalRelation,
    CausalRelationType,
)


class CausalChainBuilder:
    """Builds multi-hop causal chains and derives indirect influence relations."""

    @classmethod
    def build_downstream_chains(
        cls,
        graph: CausalGraph,
        origin_event_id: str,
        max_depth: int = 5,
    ) -> list[CausalChain]:
        """Discovers all downstream causal chains originating from origin_event_id up to max_depth."""
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")

        chains: list[CausalChain] = []

        def dfs(
            current_event_id: str,
            current_relations: list[CausalRelation],
            visited_nodes: list[str],
        ) -> None:
            if len(current_relations) >= max_depth:
                return

            outgoing = graph.get_outgoing_relations(current_event_id)
            for rel in outgoing:
                target = rel.target_event_id
                if target in visited_nodes:
                    # Cycle encountered in path!
                    continue

                new_rels = current_relations + [rel]
                new_visited = visited_nodes + [target]

                # Construct chain
                chain_event_ids = tuple(
                    [new_rels[0].source_event_id]
                    + [r.target_event_id for r in new_rels]
                )
                cum_score = sum(r.impact_score for r in new_rels) / len(new_rels)

                # Chain confidence is min confidence of constituents
                conf = CausalConfidence.STRONG
                if any(r.confidence == CausalConfidence.WEAK for r in new_rels):
                    conf = CausalConfidence.WEAK
                elif any(r.confidence == CausalConfidence.MODERATE for r in new_rels):
                    conf = CausalConfidence.MODERATE
                elif all(r.confidence == CausalConfidence.EXPLICIT for r in new_rels):
                    conf = CausalConfidence.EXPLICIT

                chain = CausalChain(
                    chain_id=f"chain:{graph.series_id}:{new_rels[0].source_event_id}:{target}:{len(new_rels)}",
                    series_id=graph.series_id,
                    origin_event_id=new_rels[0].source_event_id,
                    terminal_event_id=target,
                    start_chapter=new_rels[0].source_chapter,
                    end_chapter=new_rels[-1].target_chapter,
                    relations=tuple(new_rels),
                    event_ids=chain_event_ids,
                    cumulative_impact_score=round(cum_score, 4),
                    depth=len(new_rels),
                    confidence=conf,
                )
                chains.append(chain)

                # Recurse downstream
                dfs(target, new_rels, new_visited)

        dfs(origin_event_id, [], [origin_event_id])

        # Sort deterministically: depth -> end_chapter -> terminal_event_id -> chain_id
        chains.sort(
            key=lambda c: (
                c.depth,
                c.end_chapter,
                c.terminal_event_id,
                c.chain_id,
            )
        )
        return chains

    @classmethod
    def build_upstream_chains(
        cls,
        graph: CausalGraph,
        target_event_id: str,
        max_depth: int = 5,
    ) -> list[CausalChain]:
        """Discovers all upstream causal chains leading into target_event_id up to max_depth."""
        if max_depth < 1:
            raise ValueError("max_depth must be at least 1")

        chains: list[CausalChain] = []

        def dfs_backwards(
            current_event_id: str,
            current_relations: list[CausalRelation],
            visited_nodes: list[str],
        ) -> None:
            if len(current_relations) >= max_depth:
                return

            incoming = graph.get_incoming_relations(current_event_id)
            for rel in incoming:
                source = rel.source_event_id
                if source in visited_nodes:
                    continue

                # Prepend relation
                new_rels = [rel] + current_relations
                new_visited = [source] + visited_nodes

                chain_event_ids = tuple(
                    [new_rels[0].source_event_id]
                    + [r.target_event_id for r in new_rels]
                )
                cum_score = sum(r.impact_score for r in new_rels) / len(new_rels)

                conf = CausalConfidence.STRONG
                if any(r.confidence == CausalConfidence.WEAK for r in new_rels):
                    conf = CausalConfidence.WEAK
                elif any(r.confidence == CausalConfidence.MODERATE for r in new_rels):
                    conf = CausalConfidence.MODERATE
                elif all(r.confidence == CausalConfidence.EXPLICIT for r in new_rels):
                    conf = CausalConfidence.EXPLICIT

                chain = CausalChain(
                    chain_id=f"chain:{graph.series_id}:{source}:{target_event_id}:{len(new_rels)}",
                    series_id=graph.series_id,
                    origin_event_id=source,
                    terminal_event_id=target_event_id,
                    start_chapter=new_rels[0].source_chapter,
                    end_chapter=new_rels[-1].target_chapter,
                    relations=tuple(new_rels),
                    event_ids=chain_event_ids,
                    cumulative_impact_score=round(cum_score, 4),
                    depth=len(new_rels),
                    confidence=conf,
                )
                chains.append(chain)

                dfs_backwards(source, new_rels, new_visited)

        dfs_backwards(target_event_id, [], [target_event_id])

        chains.sort(
            key=lambda c: (
                c.depth,
                c.start_chapter,
                c.origin_event_id,
                c.chain_id,
            )
        )
        return chains

    @classmethod
    def derive_indirect_relations(
        cls,
        graph: CausalGraph,
        max_hops: int = 3,
    ) -> list[CausalRelation]:
        """Derives transitive INDIRECT_INFLUENCE relations for paths of length >= 2."""
        indirect_relations: list[CausalRelation] = []

        all_rels = graph.get_all_relations()
        source_nodes = sorted(list({r.source_event_id for r in all_rels}))

        for src in source_nodes:
            downstream = cls.build_downstream_chains(graph, src, max_depth=max_hops)
            for chain in downstream:
                if chain.depth >= 2:
                    origin = chain.origin_event_id
                    terminal = chain.terminal_event_id

                    # If there's already a direct edge from origin to terminal, don't overwrite
                    direct_exists = any(
                        r.source_event_id == origin and r.target_event_id == terminal
                        for r in graph.get_outgoing_relations(origin)
                    )

                    evidence = CausalEvidenceReference(
                        rule_id="RULE_TRANSITIVE_INDIRECT_INFLUENCE",
                        explanation_code=f"CHAIN_DEPTH_{chain.depth}",
                        source_event_ids=tuple(chain.event_ids[:-1]),
                        target_event_id=terminal,
                        temporal_basis=f"Ch {chain.start_chapter} <= Ch {chain.end_chapter}",
                        state_basis=f"path_length:{chain.depth}",
                    )

                    rel = CausalRelation(
                        relation_id=f"causal:{graph.series_id}:{origin}:{terminal}:indirect",
                        series_id=graph.series_id,
                        source_event_id=origin,
                        target_event_id=terminal,
                        relation_type=CausalRelationType.INDIRECT_INFLUENCE,
                        derivation_type=CausalDerivationType.DERIVED_INDIRECT,
                        confidence=CausalConfidence.MODERATE,
                        source_chapter=chain.start_chapter,
                        target_chapter=chain.end_chapter,
                        evidence=evidence,
                        impact_score=compute_causal_impact_score(
                            CausalRelationType.INDIRECT_INFLUENCE,
                            CausalConfidence.MODERATE,
                            affected_entity_count=len(chain.event_ids),
                        ),
                        metadata={"path": list(chain.event_ids)},
                    )
                    indirect_relations.append(rel)

        # Sort deterministically
        indirect_relations.sort(
            key=lambda r: (
                r.source_chapter,
                r.target_chapter,
                r.source_event_id,
                r.target_event_id,
                r.relation_id,
            )
        )
        return indirect_relations
