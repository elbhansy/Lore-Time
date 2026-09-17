import uuid

from packages.domain.entities.power_system import PowerSystem
from packages.domain.repositories.power_system_repository import PowerSystemRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import SeriesNotFound


class GetPowerSystemsUseCase:
    def __init__(
        self, power_system_repo: PowerSystemRepository, series_repo: SeriesRepository
    ):
        self.power_system_repo = power_system_repo
        self.series_repo = series_repo

    def execute(self, series_id: uuid.UUID) -> list[PowerSystem]:
        s_id = EntityId(series_id)
        if not self.series_repo.get(s_id):
            raise SeriesNotFound(f"Series with id {series_id} not found")

        return self.power_system_repo.get_all_by_series(s_id)
