from sqlalchemy.orm import Session

from infrastructure.database.models.ingestion.entity_alias import EntityAliasModel
from packages.domain.ingestion.entity_resolution import EntityAlias
from packages.domain.repositories.entity_alias_repository import EntityAliasRepository


class SQLAlchemyEntityAliasRepository(EntityAliasRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: EntityAliasModel) -> EntityAlias:
        return EntityAlias(
            id=str(model.id),
            series_id=str(model.series_id),
            entity_id=str(model.entity_id),
            entity_type=model.entity_type,
            alias=model.alias,
            normalized_alias=model.normalized_alias,
            source=model.source,
            confidence=model.confidence,
            active=model.active,
        )

    def get_by_normalized_alias(
        self, series_id: str, entity_type: str, normalized_alias: str
    ) -> list[EntityAlias]:
        models = (
            self.session.query(EntityAliasModel)
            .filter(
                EntityAliasModel.series_id == series_id,
                EntityAliasModel.entity_type == entity_type,
                EntityAliasModel.normalized_alias == normalized_alias,
                EntityAliasModel.active == True,
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def save(self, alias: EntityAlias) -> None:
        model = self.session.query(EntityAliasModel).filter_by(id=alias.id).first()
        if not model:
            model = EntityAliasModel(id=alias.id)
            self.session.add(model)

        model.series_id = alias.series_id
        model.entity_id = alias.entity_id
        model.entity_type = alias.entity_type
        model.alias = alias.alias
        model.normalized_alias = alias.normalized_alias
        model.source = alias.source
        model.confidence = alias.confidence
        model.active = alias.active

    def deactivate(self, alias_id: str) -> None:
        model = self.session.query(EntityAliasModel).filter_by(id=alias_id).first()
        if model:
            model.active = False
