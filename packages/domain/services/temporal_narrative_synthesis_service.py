"""Temporal Narrative Synthesis Domain Service (Phase 5.3 Milestone 5.3.16).

Domain service orchestrating:
1. Retrieval of causal graph via CausalIntelligenceService
2. Retrieval of character arcs via NarrativeIntelligenceEngine
3. Synthesis of event and character narrative explanations via NarrativeCausalSynthesizer
"""

from packages.domain.narrative.models import CharacterArc
from packages.domain.services.causal_intelligence_service import (
    CausalIntelligenceService,
)
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.services.narrative_intelligence_engine import (
    NarrativeIntelligenceEngine,
)
from packages.domain.state.world_state import WorldState
from packages.domain.synthesis.models import TemporalNarrativeCausalExplanation
from packages.domain.synthesis.synthesizer import NarrativeCausalSynthesizer


class TemporalNarrativeSynthesisService:
    """Domain service orchestrating temporal narrative causal synthesis."""

    def __init__(
        self,
        causal_service: CausalIntelligenceService | None = None,
        narrative_engine: NarrativeIntelligenceEngine | None = None,
    ):
        self.causal_service = causal_service or CausalIntelligenceService()
        self.narrative_engine = narrative_engine or NarrativeIntelligenceEngine()

    def explain_event_narrative(
        self,
        series_id: str,
        event_id: str,
        reader_chapter: int,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
        """Synthesizes upstream causes and downstream narrative arc impacts for an event."""
        # 1. Build causal graph
        graph = self.causal_service.build_causal_graph(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )

        # 2. Derive Character Arcs for entities involved in visible events
        visible_envs = [
            e for e in envelopes if e.chapter_number.value <= reader_chapter
        ]
        involved_chars: set[str] = set()
        for env in visible_envs:
            if env.event.subject_id:
                involved_chars.add(str(env.event.subject_id.value))
            if env.event.target_id:
                involved_chars.add(str(env.event.target_id.value))

        arcs_by_char: dict[str, CharacterArc] = {}
        for cid in sorted(list(involved_chars)):
            arc = self.narrative_engine.derive_character_arc(
                series_id=series_id,
                character_id=cid,
                reader_chapter=reader_chapter,
                envelopes=envelopes,
                world_state=world_state,
            )
            arcs_by_char[cid] = arc

        # 3. Perform narrative causal synthesis
        return NarrativeCausalSynthesizer.synthesize_event_explanation(
            series_id=series_id,
            event_id=event_id,
            reader_chapter=reader_chapter,
            graph=graph,
            envelopes=envelopes,
            arcs_by_character=arcs_by_char,
            max_depth=max_depth,
        )

    def explain_character_narrative_causality(
        self,
        series_id: str,
        character_id: str,
        reader_chapter: int,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
        """Synthesizes character arc milestones, turning points, and causal triggers."""
        # 1. Build causal graph
        graph = self.causal_service.build_causal_graph(
            series_id=series_id,
            envelopes=envelopes,
            world_state=world_state,
            reader_chapter=reader_chapter,
        )

        # 2. Derive character arc
        arc = self.narrative_engine.derive_character_arc(
            series_id=series_id,
            character_id=character_id,
            reader_chapter=reader_chapter,
            envelopes=envelopes,
            world_state=world_state,
        )

        # 3. Perform narrative causal synthesis
        return NarrativeCausalSynthesizer.synthesize_character_explanation(
            series_id=series_id,
            character_id=character_id,
            reader_chapter=reader_chapter,
            graph=graph,
            character_arc=arc,
            envelopes=envelopes,
            max_depth=max_depth,
        )
