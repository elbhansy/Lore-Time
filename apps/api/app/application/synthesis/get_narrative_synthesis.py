"""Application use cases for Temporal Narrative Causal Synthesis (Phase 5.3)."""

import logging
import time
import uuid

from apps.api.app.application.exceptions import (
    CharacterNotFound,
    EntityNotFound,
    InvalidChapter,
    SeriesNotFound,
)
from apps.api.app.core.cache import CacheService, get_cache_service
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.services.temporal_narrative_synthesis_service import (
    TemporalNarrativeSynthesisService,
)
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.synthesis.models import TemporalNarrativeCausalExplanation
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

logger = logging.getLogger("timeline.application")


class GetEventNarrativeExplanationUseCase:
    """Synthesizes upstream causes and downstream narrative consequences for an event."""

    def __init__(
        self,
        series_repo: SeriesRepository,
        event_repo: EventRepository,
        world_state_builder: WorldStateBuilder,
        synthesis_service: TemporalNarrativeSynthesisService,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.event_repo = event_repo
        self.world_state_builder = world_state_builder
        self.synthesis_service = synthesis_service
        self.cache_service = cache_service or get_cache_service()

    def execute(
        self,
        series_id: uuid.UUID,
        event_id: str,
        reader_chapter: int,
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_eid = EntityId(series_id)
        chapter_val = ChapterNumber(reader_chapter)

        # 1. Validate series existence
        series = self.series_repo.get(series_eid)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        # 2. Check event existence
        try:
            ev_uuid = uuid.UUID(event_id)
            ev_eid = EntityId(ev_uuid)
        except ValueError:
            ev_eid = EntityId(event_id)

        target_event = self.event_repo.get(ev_eid)
        if not target_event or (
            target_event.series_id
            and str(target_event.series_id.value) != str(series_id)
        ):
            raise EntityNotFound(f"Event {event_id} not found in series {series_id}")

        def compute_synthesis() -> TemporalNarrativeCausalExplanation:
            start_time = time.perf_counter()

            # Retrieve canonical events visible at reader_chapter
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )

            # Materialize WorldState at reader_chapter
            world_state = self.world_state_builder.build(
                series_id=series_eid,
                envelopes=envelopes,
                reader_chapter=chapter_val,
            )

            explanation = self.synthesis_service.explain_event_narrative(
                series_id=str(series_id),
                event_id=event_id,
                reader_chapter=reader_chapter,
                envelopes=envelopes,
                world_state=world_state,
                max_depth=max_depth,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Event narrative synthesized for event %s in series %s at ch %s (%sms)",
                event_id,
                series_id,
                reader_chapter,
                duration_ms,
                extra={
                    "event": "event_narrative.synthesized",
                    "series_id": str(series_id),
                    "event_id": str(event_id),
                    "reader_chapter": reader_chapter,
                    "max_depth": max_depth,
                    "duration_ms": duration_ms,
                    "outcome": "success",
                },
            )
            return explanation

        # 3. Cache Integration
        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource=f"event_narrative:{event_id}:d{max_depth}",
                compute_fn=compute_synthesis,
                reader_chapter=reader_chapter,
            )

        return compute_synthesis()


class GetCharacterNarrativeCausalityUseCase:
    """Synthesizes character arc milestones, turning points, and causal triggers."""

    def __init__(
        self,
        series_repo: SeriesRepository,
        character_repo: CharacterRepository,
        event_repo: EventRepository,
        world_state_builder: WorldStateBuilder,
        synthesis_service: TemporalNarrativeSynthesisService,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.character_repo = character_repo
        self.event_repo = event_repo
        self.world_state_builder = world_state_builder
        self.synthesis_service = synthesis_service
        self.cache_service = cache_service or get_cache_service()

    def execute(
        self,
        series_id: uuid.UUID,
        character_id: str,
        reader_chapter: int,
        max_depth: int = 4,
    ) -> TemporalNarrativeCausalExplanation:
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

        def compute_char_synthesis() -> TemporalNarrativeCausalExplanation:
            start_time = time.perf_counter()

            # Retrieve canonical events visible at reader_chapter
            envelopes = self.event_repo.get_all_by_series(
                series_eid, to_chapter=chapter_val
            )

            # Materialize WorldState at reader_chapter
            world_state = self.world_state_builder.build(
                series_id=series_eid,
                envelopes=envelopes,
                reader_chapter=chapter_val,
            )

            explanation = self.synthesis_service.explain_character_narrative_causality(
                series_id=str(series_id),
                character_id=str(character.id.value),
                reader_chapter=reader_chapter,
                envelopes=envelopes,
                world_state=world_state,
                max_depth=max_depth,
            )

            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "Character narrative causality synthesized for character %s in series %s at ch %s (%sms)",
                character_id,
                series_id,
                reader_chapter,
                duration_ms,
                extra={
                    "event": "character_narrative_causality.synthesized",
                    "series_id": str(series_id),
                    "character_id": str(character_id),
                    "reader_chapter": reader_chapter,
                    "max_depth": max_depth,
                    "duration_ms": duration_ms,
                    "outcome": "success",
                },
            )
            return explanation

        # 3. Cache Integration
        if self.cache_service and self.cache_service.is_enabled:
            return self.cache_service.get_or_compute(
                series_id=series_id,
                resource=f"character_narrative_causality:{character.id.value}:d{max_depth}",
                compute_fn=compute_char_synthesis,
                reader_chapter=reader_chapter,
            )

        return compute_char_synthesis()
