"""Get Character Arc Application Use Case (Phase 5.1).

Orchestrates:
1. Validating series and character existence
2. Enforcing readerChapter temporal boundary
3. Loading relevant canonical event stream from EventRepository
4. Materializing WorldState at readerChapter
5. Invoking NarrativeIntelligenceEngine
6. Serving with CacheService integration
"""

import logging
import time
import uuid

from apps.api.app.application.exceptions import (
    CharacterNotFound,
    InvalidChapter,
    SeriesNotFound,
)
from apps.api.app.core.cache import CacheService, get_cache_service
from packages.domain.narrative.models import CharacterArc
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.services.narrative_intelligence_engine import (
    NarrativeIntelligenceEngine,
)
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

logger = logging.getLogger("timeline.application")


class GetCharacterArcUseCase:
    """Application use case for retrieving the deterministic CharacterArc for a character."""

    def __init__(
        self,
        series_repo: SeriesRepository,
        character_repo: CharacterRepository,
        event_repo: EventRepository,
        world_state_builder: WorldStateBuilder,
        narrative_engine: NarrativeIntelligenceEngine,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.character_repo = character_repo
        self.event_repo = event_repo
        self.world_state_builder = world_state_builder
        self.narrative_engine = narrative_engine
        self.cache_service = cache_service or get_cache_service()

    def execute(
        self, series_id: uuid.UUID, character_id: str, reader_chapter: int
    ) -> CharacterArc:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_eid = EntityId(series_id)
        chapter_val = ChapterNumber(reader_chapter)

        # 1. Validate series existence
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        # 2. Validate character existence in series
        try:
            char_uuid = uuid.UUID(character_id)
            char_eid = EntityId(char_uuid)
        except ValueError:
            char_eid = EntityId(character_id)

        character = self.character_repo.get(char_eid)
        if not character or (
            character.series_id and str(character.series_id.value) != str(series_id)
        ):
            raise CharacterNotFound(
                f"Character {character_id} not found in series {series_id}"
            )

        def compute_arc() -> CharacterArc:
            start_time = time.perf_counter()

            # Retrieve all canonical events in this series up to reader_chapter
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )

            # Materialize WorldState at reader_chapter
            world_state = self.world_state_builder.build(
                series_id=series_eid,
                envelopes=envelopes,
                reader_chapter=chapter_val,
            )

            # Derive the character arc
            arc = self.narrative_engine.derive_character_arc(
                series_id=str(series_id),
                character_id=str(character.id.value),
                reader_chapter=reader_chapter,
                envelopes=envelopes,
                world_state=world_state,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Character arc derived for character %s in series %s at chapter %s (%s milestones, %sms)",
                character_id,
                series_id,
                reader_chapter,
                len(arc.milestones),
                duration_ms,
                extra={
                    "event": "character_arc.derived",
                    "series_id": str(series_id),
                    "character_id": str(character_id),
                    "reader_chapter": reader_chapter,
                    "milestones_count": len(arc.milestones),
                    "duration_ms": duration_ms,
                    "outcome": "success",
                },
            )
            return arc

        # 3. Cache Integration
        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource=f"character_arc:{character.id.value}",
                compute_fn=compute_arc,
                reader_chapter=reader_chapter,
            )

        return compute_arc()
