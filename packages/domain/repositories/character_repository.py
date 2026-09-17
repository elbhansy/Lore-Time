from abc import ABC, abstractmethod

from ..entities.character import Character
from ..value_objects.entity_id import EntityId


class CharacterRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> Character | None:
        pass

    @abstractmethod
    def get_all_by_series(self, series_id: EntityId) -> list[Character]:
        pass

    @abstractmethod
    def save(self, character: Character) -> None:
        pass
