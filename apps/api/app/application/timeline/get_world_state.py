import logging
import time
import uuid

from apps.api.app.core.cache import CacheService, get_cache_service
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.state.world_state import WorldState
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import InvalidChapter, SeriesNotFound

logger = logging.getLogger("timeline.application")


class GetWorldStateUseCase:
    def __init__(
        self,
        series_repo: SeriesRepository,
        event_repo: EventRepository,
        world_state_builder: WorldStateBuilder,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.event_repo = event_repo
        self.world_state_builder = world_state_builder
        self.cache_service = cache_service or get_cache_service()

    def execute(self, series_id: uuid.UUID, reader_chapter: int) -> WorldState:
        if reader_chapter < 1:
            raise InvalidChapter("Chapter number must be positive")

        series_entity_id = EntityId(series_id)
        chapter_val = ChapterNumber(reader_chapter)

        series = self.series_repo.get(series_entity_id)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        def compute_world_state() -> WorldState:
            start_time = time.perf_counter()
            envelopes = self.event_repo.get_all_by_series(
                series_entity_id, to_chapter=chapter_val
            )

            # Build the world state
            ws = self.world_state_builder.build(
                series_id=series_entity_id,
                envelopes=envelopes,
                reader_chapter=chapter_val,
            )
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.info(
                "WorldState build completed for series %s at chapter %s (%s events, %sms)",
                series_id,
                reader_chapter,
                len(envelopes),
                duration_ms,
                extra={
                    "event": "world_state.build.completed",
                    "series_id": str(series_id),
                    "reader_chapter": reader_chapter,
                    "operation": "build_world_state",
                    "duration_ms": duration_ms,
                    "outcome": "success",
                },
            )
            return ws

        return self.cache_service.get_or_compute(
            series_id=series_id,
            resource="world_state",
            compute_fn=compute_world_state,
            reader_chapter=reader_chapter,
        )
