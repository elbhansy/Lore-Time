"""Narrative Intelligence Engine domain service (Phase 5.1).

Pure, framework-agnostic domain service for deriving narrative arcs and structural insights.
"""

from packages.domain.narrative.character_arc_builder import CharacterArcBuilder
from packages.domain.narrative.models import CharacterArc
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.state.world_state import WorldState


class NarrativeIntelligenceEngine:
    """Domain service for evaluating narrative arcs, milestones, turning points, and phases."""

    def __init__(self):
        pass

    def derive_character_arc(
        self,
        series_id: str,
        character_id: str,
        reader_chapter: int,
        envelopes: list[EventEnvelope],
        world_state: WorldState | None = None,
    ) -> CharacterArc:
        """Derives a deterministic CharacterArc aggregate for the given character up to reader_chapter."""
        return CharacterArcBuilder.build_arc(
            series_id=series_id,
            character_id=character_id,
            reader_chapter=reader_chapter,
            envelopes=envelopes,
            world_state=world_state,
        )
