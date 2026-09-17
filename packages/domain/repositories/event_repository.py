from abc import ABC, abstractmethod

from ..entities.event import Event
from ..events.event_query import EventQuery
from ..services.event_ordering import EventEnvelope
from ..value_objects.chapter_number import ChapterNumber
from ..value_objects.entity_id import EntityId


class EventRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> Event | None:
        pass

    @abstractmethod
    def get_by_chapter(
        self, series_id: EntityId, chapter_number: ChapterNumber
    ) -> list[EventEnvelope]:
        pass

    @abstractmethod
    def get_by_chapter_range(
        self,
        series_id: EntityId,
        from_chapter: ChapterNumber,
        to_chapter: ChapterNumber,
    ) -> list[EventEnvelope]:
        pass

    @abstractmethod
    def get_all_by_series(
        self, series_id: EntityId, to_chapter: ChapterNumber | None = None
    ) -> list[EventEnvelope]:
        pass

    @abstractmethod
    def query(self, query: EventQuery) -> list[Event]:
        pass

    @abstractmethod
    def count(self, query: EventQuery) -> int:
        pass

    @abstractmethod
    def save(self, event: Event) -> None:
        pass
