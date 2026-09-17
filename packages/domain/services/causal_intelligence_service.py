"""Causal Intelligence Domain Service (Phase 5.2 Milestone 5.2.16).

Pure domain service exposing clean APIs for causal graph generation, chain traversal,
upstream cause discovery, downstream effect discovery, and character explanations.
Has zero dependencies on FastAPI, SQLAlchemy, HTTP, or presentation models.
"""

from packages.domain.causality.causal_graph import CausalGraph
from packages.domain.causality.chain_builder import CausalChainBuilder
from packages.domain.causality.character_explainer import (
    CharacterCausalExplainer,
    CharacterCausalExplanation,
)
from packages.domain.causality.derivation_engine import CausalDerivationEngine
from packages.domain.causality.models import (
    CausalChain,
)
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.state.world_state import WorldState


class CausalIntelligenceService:
    """Domain service for deterministic causal reasoning over canonical temporal data."""

    def __init__(self, max_traversal_depth: int = 5):
        self.max_traversal_depth = max_traversal_depth

    def build_causal_graph(
        self,
        series_id: str,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        reader_chapter: int | None = None,
    ) -> CausalGraph:
        """Derives all relations and populates a CausalGraph."""
        relations = CausalDerivationEngine.derive_relations(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )

        graph = CausalGraph(series_id=series_id, reader_chapter=reader_chapter)
        for rel in relations:
            graph.add_relation(rel)

        return graph

    def get_downstream_effects(
        self,
        series_id: str,
        event_id: str,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        reader_chapter: int | None = None,
        max_depth: int | None = None,
    ) -> list[CausalChain]:
        """Returns all downstream causal chains propagating from event_id."""
        graph = self.build_causal_graph(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )
        depth = max_depth or self.max_traversal_depth
        return CausalChainBuilder.build_downstream_chains(
            graph, event_id, max_depth=depth
        )

    def get_upstream_causes(
        self,
        series_id: str,
        event_id: str,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        reader_chapter: int | None = None,
        max_depth: int | None = None,
    ) -> list[CausalChain]:
        """Returns all upstream causal chains explaining the causes of event_id."""
        graph = self.build_causal_graph(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )
        depth = max_depth or self.max_traversal_depth
        return CausalChainBuilder.build_upstream_chains(
            graph, event_id, max_depth=depth
        )

    def explain_character_causality(
        self,
        series_id: str,
        character_id: str,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        reader_chapter: int = 1,
        max_depth: int | None = None,
    ) -> CharacterCausalExplanation:
        """Explains upstream causes and downstream consequences for a character."""
        graph = self.build_causal_graph(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )
        depth = max_depth or self.max_traversal_depth
        return CharacterCausalExplainer.explain(
            character_id=character_id,
            series_id=series_id,
            reader_chapter=reader_chapter,
            graph=graph,
            envelopes=envelopes,
            max_depth=depth,
        )
