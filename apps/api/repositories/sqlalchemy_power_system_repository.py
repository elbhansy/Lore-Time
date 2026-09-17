from sqlalchemy.orm import Session

from infrastructure.database.models.power_system import PowerSystemModel
from packages.domain.entities.power_system import PowerSystem
from packages.domain.repositories.power_system_repository import PowerSystemRepository
from packages.domain.value_objects.entity_id import EntityId


class SQLAlchemyPowerSystemRepository(PowerSystemRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: PowerSystemModel) -> PowerSystem:
        return PowerSystem(
            id=EntityId(model.id),
            series_id=EntityId(model.series_id),
            name=model.name,
            slug=model.slug,
            description=model.description,
        )

    def get(self, id: EntityId) -> PowerSystem | None:
        model = self.session.query(PowerSystemModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_all_by_series(self, series_id: EntityId) -> list[PowerSystem]:
        models = (
            self.session.query(PowerSystemModel)
            .filter_by(series_id=series_id.value)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def save(self, system: PowerSystem) -> None:
        model = (
            self.session.query(PowerSystemModel).filter_by(id=system.id.value).first()
        )
        if not model:
            model = PowerSystemModel(id=system.id.value)
            self.session.add(model)

        model.series_id = system.series_id.value
        model.name = system.name
        model.slug = system.slug
        model.description = system.description
        self.session.flush()
