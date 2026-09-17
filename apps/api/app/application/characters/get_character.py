import uuid

from packages.domain.entities.character import Character
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.state.character_state import CharacterState
from packages.domain.value_objects.entity_id import EntityId

from ..exceptions import CharacterNotFound
from ..timeline.get_world_state import GetWorldStateUseCase


class GetCharacterUseCase:
    def __init__(
        self,
        character_repo: CharacterRepository,
        get_world_state_uc: GetWorldStateUseCase,
    ):
        self.character_repo = character_repo
        self.get_world_state_uc = get_world_state_uc

    def execute(
        self, series_id: uuid.UUID, character_id: uuid.UUID, reader_chapter: int
    ) -> tuple[Character, CharacterState]:
        # 1. Get Domain Entity
        char_entity = self.character_repo.get(EntityId(character_id))
        if not char_entity or char_entity.series_id.value != series_id:
            raise CharacterNotFound(
                f"Character with id {character_id} not found in series {series_id}"
            )

        # 2. Get WorldState at the specific chapter
        world_state = self.get_world_state_uc.execute(series_id, reader_chapter)

        # 3. Extract the CharacterState
        char_state = world_state.characters.get(EntityId(character_id))
        if not char_state:
            raise CharacterNotFound(
                f"Character state for {character_id} not found at chapter {reader_chapter}"
            )

        return char_entity, char_state
