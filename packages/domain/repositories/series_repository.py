from abc import ABC, abstractmethod

from ..entities.series import Series
from ..value_objects.entity_id import EntityId


class SeriesRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> Series | None:
        pass

    @abstractmethod
    def get_by_slug(self, slug: str) -> Series | None:
        pass

    @abstractmethod
    def save(self, series: Series) -> None:
        pass
