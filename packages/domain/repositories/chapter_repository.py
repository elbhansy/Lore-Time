from abc import ABC, abstractmethod

from ..entities.chapter import Chapter
from ..value_objects.entity_id import EntityId


class ChapterRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> Chapter | None:
        pass

    @abstractmethod
    def save(self, chapter: Chapter) -> None:
        pass
