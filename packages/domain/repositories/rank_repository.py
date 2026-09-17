from abc import ABC, abstractmethod

from ..entities.rank import Rank
from ..value_objects.entity_id import EntityId


class RankRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> Rank | None:
        pass

    @abstractmethod
    def get_by_system_id(self, power_system_id: EntityId) -> list[Rank]:
        pass

    @abstractmethod
    def get_visible_ranks(
        self, power_system_id: EntityId, reader_chapter: int
    ) -> list[Rank]:
        pass

    @abstractmethod
    def save(self, rank: Rank) -> None:
        pass
