"""Character-Centered Causal Explainer (Phase 5.2 Milestone 5.2.15).

Explains upstream causes and downstream consequences centered on a specific character.
"""

from dataclasses import dataclass, field
from typing import Any

from packages.domain.causality.causal_graph import CausalGraph
from packages.domain.causality.chain_builder import CausalChainBuilder
from packages.domain.causality.models import (
    CausalChain,
    CausalRelation,
)
from packages.domain.services.event_ordering import EventEnvelope


@dataclass(frozen=True)
class CharacterCausalExplanation:
    """Explains upstream causes and downstream consequences for a character."""

    character_id: str
    series_id: str
    reader_chapter: int
    central_event_ids: tuple[str, ...]
    upstream_relations: tuple[CausalRelation, ...]
    downstream_relations: tuple[CausalRelation, ...]
    upstream_chains: tuple[CausalChain, ...]
    downstream_chains: tuple[CausalChain, ...]
    affected_entities: tuple[str, ...]
    summary: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "character_id": self.character_id,
            "series_id": self.series_id,
            "reader_chapter": self.reader_chapter,
            "central_event_ids": list(self.central_event_ids),
            "upstream_relations": [r.to_dict() for r in self.upstream_relations],
            "downstream_relations": [r.to_dict() for r in self.downstream_relations],
            "upstream_chains": [c.to_dict() for c in self.upstream_chains],
            "downstream_chains": [c.to_dict() for c in self.downstream_chains],
            "affected_entities": list(self.affected_entities),
            "summary": dict(self.summary),
        }


class CharacterCausalExplainer:
    """Builds structured causal explanations centered around a character."""

    @classmethod
    def explain(
        cls,
        character_id: str,
        series_id: str,
        reader_chapter: int,
        graph: CausalGraph,
        envelopes: list[EventEnvelope],
        max_depth: int = 3,
    ) -> CharacterCausalExplanation:
        """Explains upstream and downstream causality for the character up to reader_chapter."""
        # 1. Identify all visible events directly concerning this character
        char_events = [
            env
            for env in envelopes
            if env.chapter_number.value <= reader_chapter
            and (
                (
                    env.event.subject_id
                    and str(env.event.subject_id.value) == character_id
                )
                or (
                    env.event.target_id
                    and str(env.event.target_id.value) == character_id
                )
            )
        ]

        central_ids = tuple(
            sorted(list({str(env.event.id.value) for env in char_events}))
        )

        upstream_rels_map: dict[str, CausalRelation] = {}
        downstream_rels_map: dict[str, CausalRelation] = {}
        upstream_chains: list[CausalChain] = []
        downstream_chains: list[CausalChain] = []
        affected_entities_set: set[str] = set()

        for eid in central_ids:
            # Immediate incoming & outgoing
            for rel in graph.get_incoming_relations(eid):
                upstream_rels_map[rel.relation_id] = rel
                affected_entities_set.update(rel.affected_entity_ids)

            for rel in graph.get_outgoing_relations(eid):
                downstream_rels_map[rel.relation_id] = rel
                affected_entities_set.update(rel.affected_entity_ids)

            # Upstream multi-hop chains
            up_chains = CausalChainBuilder.build_upstream_chains(
                graph, eid, max_depth=max_depth
            )
            upstream_chains.extend(up_chains)

            # Downstream multi-hop chains
            down_chains = CausalChainBuilder.build_downstream_chains(
                graph, eid, max_depth=max_depth
            )
            downstream_chains.extend(down_chains)

        sorted_upstream_rels = tuple(
            sorted(
                list(upstream_rels_map.values()),
                key=lambda r: (r.source_chapter, r.source_event_id, r.relation_id),
            )
        )
        sorted_downstream_rels = tuple(
            sorted(
                list(downstream_rels_map.values()),
                key=lambda r: (r.target_chapter, r.target_event_id, r.relation_id),
            )
        )

        # Sort and deduplicate chains
        seen_chain_ids: set[str] = set()
        deduped_up_chains = []
        for c in upstream_chains:
            if c.chain_id not in seen_chain_ids:
                seen_chain_ids.add(c.chain_id)
                deduped_up_chains.append(c)

        seen_chain_ids.clear()
        deduped_down_chains = []
        for c in downstream_chains:
            if c.chain_id not in seen_chain_ids:
                seen_chain_ids.add(c.chain_id)
                deduped_down_chains.append(c)

        summary = {
            "total_central_events": len(central_ids),
            "total_upstream_causes": len(sorted_upstream_rels),
            "total_downstream_effects": len(sorted_downstream_rels),
            "total_upstream_chains": len(deduped_up_chains),
            "total_downstream_chains": len(deduped_down_chains),
        }

        return CharacterCausalExplanation(
            character_id=character_id,
            series_id=series_id,
            reader_chapter=reader_chapter,
            central_event_ids=central_ids,
            upstream_relations=sorted_upstream_rels,
            downstream_relations=sorted_downstream_rels,
            upstream_chains=tuple(deduped_up_chains),
            downstream_chains=tuple(deduped_down_chains),
            affected_entities=tuple(sorted(list(affected_entities_set))),
            summary=summary,
        )
