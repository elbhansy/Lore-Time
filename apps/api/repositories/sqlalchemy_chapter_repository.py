from sqlalchemy.orm import Session

from infrastructure.database.models.chapter import ChapterModel
from packages.domain.entities.chapter import Chapter
from packages.domain.repositories.chapter_repository import ChapterRepository
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


class SQLAlchemyChapterRepository(ChapterRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: ChapterModel) -> Chapter:
        return Chapter(
            id=EntityId(model.id),
            series_id=EntityId(model.series_id),
            number=ChapterNumber(model.number),
            title=model.title,
        )

    def get(self, id: EntityId) -> Chapter | None:
        model = self.session.query(ChapterModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def save(self, chapter: Chapter) -> None:
        model = self.session.query(ChapterModel).filter_by(id=chapter.id.value).first()
        if not model:
            model = ChapterModel(id=chapter.id.value)
            self.session.add(model)

        model.series_id = chapter.series_id.value
        model.number = chapter.number.value
        model.title = chapter.title
