from sqlalchemy.orm import Session

from infrastructure.database.models.series import SeriesModel
from packages.domain.entities.series import Series
from packages.domain.repositories.series_repository import SeriesRepository
from packages.domain.value_objects.entity_id import EntityId


class SQLAlchemySeriesRepository(SeriesRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: SeriesModel) -> Series:
        return Series(
            id=EntityId(model.id),
            title=model.title,
            slug=model.slug,
            total_chapters=model.total_chapters,
        )

    def get(self, id: EntityId) -> Series | None:
        model = self.session.query(SeriesModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_by_slug(self, slug: str) -> Series | None:
        model = self.session.query(SeriesModel).filter_by(slug=slug).first()
        if not model:
            return None
        return self._to_domain(model)

    def save(self, series: Series) -> None:
        model = self.session.query(SeriesModel).filter_by(id=series.id.value).first()
        if not model:
            model = SeriesModel(id=series.id.value)
            self.session.add(model)

        model.title = series.title
        model.slug = series.slug
        model.total_chapters = series.total_chapters
