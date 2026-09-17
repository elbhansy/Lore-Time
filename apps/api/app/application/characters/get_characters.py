import uuid

from packages.domain.entities.character import Character
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import SeriesNotFound


class GetCharactersUseCase:
    def __init__(
        self, character_repo: CharacterRepository, series_repo: SeriesRepository
    ):
        self.character_repo = character_repo
        self.series_repo = series_repo

    def execute(self, series_id: uuid.UUID) -> list[Character]:
        s_id = EntityId(series_id)
        if not self.series_repo.get(s_id):
            raise SeriesNotFound(f"Series with id {series_id} not found")

        return self.character_repo.get_all_by_series(s_id)
