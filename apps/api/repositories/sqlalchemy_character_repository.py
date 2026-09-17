from sqlalchemy.orm import Session

from infrastructure.database.models.character import CharacterModel
from packages.domain.entities.character import Character
from packages.domain.repositories.character_repository import CharacterRepository
from packages.domain.value_objects.entity_id import EntityId


class SQLAlchemyCharacterRepository(CharacterRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: CharacterModel) -> Character:
        return Character(
            id=EntityId(model.id),
            series_id=EntityId(model.series_id),
            name=model.name,
            description=model.description,
        )

    def get(self, id: EntityId) -> Character | None:
        model = self.session.query(CharacterModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_all_by_series(self, series_id: EntityId) -> list[Character]:
        models = (
            self.session.query(CharacterModel)
            .filter_by(series_id=series_id.value)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def save(self, character: Character) -> None:
        model = (
            self.session.query(CharacterModel).filter_by(id=character.id.value).first()
        )
        if not model:
            model = CharacterModel(id=character.id.value)
            self.session.add(model)

        model.series_id = character.series_id.value
        model.name = character.name
        model.description = character.description
