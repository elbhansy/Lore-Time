from abc import ABC, abstractmethod

from ..entities.power_system import PowerSystem
from ..value_objects.entity_id import EntityId


class PowerSystemRepository(ABC):
    @abstractmethod
    def get(self, id: EntityId) -> PowerSystem | None:
        pass

    @abstractmethod
    def get_all_by_series(self, series_id: EntityId) -> list[PowerSystem]:
        pass

    @abstractmethod
    def save(self, system: PowerSystem) -> None:
        pass
