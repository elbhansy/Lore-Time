import uuid

from apps.api.app.core.cache import CacheService, get_cache_service
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import InvalidChapter, SeriesNotFound


class GetTimelineEventsUseCase:
    def __init__(
        self,
        series_repo: SeriesRepository,
        event_repo: EventRepository,
        cache_service: CacheService | None = None,
    ):
        self.series_repo = series_repo
        self.event_repo = event_repo
        self.cache_service = cache_service or get_cache_service()

    def execute(
        self,
        series_id: uuid.UUID,
        reader_chapter: int,
        from_chapter: int,
        to_chapter: int,
    ) -> list[EventEnvelope]:
        if reader_chapter < 1 or from_chapter < 1 or to_chapter < 1:
            raise InvalidChapter("Chapter numbers must be positive")

        if to_chapter > reader_chapter:
            # We strictly bound the maximum requested chapter by the reader's chapter
            # to enforce the Spoiler Firewall at the API level as well.
            to_chapter = reader_chapter

        if from_chapter > to_chapter:
            return []

        series_entity_id = EntityId(series_id)
        series = self.series_repo.get(series_entity_id)
        if not series:
            raise SeriesNotFound(f"Series with id {series_id} not found")

        def compute_envelopes() -> list[EventEnvelope]:
            return self.event_repo.get_by_chapter_range(
                series_id=series_entity_id,
                from_chapter=ChapterNumber(from_chapter),
                to_chapter=ChapterNumber(to_chapter),
            )

        return self.cache_service.get_or_compute(
            series_id=series_id,
            resource="timeline",
            compute_fn=compute_envelopes,
            reader_chapter=reader_chapter,
            query_params={"from": from_chapter, "to": to_chapter},
        )
