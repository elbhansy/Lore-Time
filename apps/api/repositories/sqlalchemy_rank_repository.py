from sqlalchemy.orm import Session

from infrastructure.database.models.rank import RankModel
from packages.domain.entities.rank import Rank
from packages.domain.repositories.rank_repository import RankRepository
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


class SQLAlchemyRankRepository(RankRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: RankModel) -> Rank:
        return Rank(
            id=EntityId(model.id),
            power_system_id=EntityId(model.power_system_id),
            name=model.name,
            slug=model.slug,
            order=model.order,
            introduced_chapter=ChapterNumber(model.introduced_chapter),
            description=model.description,
            parent_rank_id=EntityId(model.parent_rank_id)
            if model.parent_rank_id
            else None,
        )

    def get(self, id: EntityId) -> Rank | None:
        model = self.session.query(RankModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_by_system_id(self, power_system_id: EntityId) -> list[Rank]:
        models = (
            self.session.query(RankModel)
            .filter_by(power_system_id=power_system_id.value)
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_visible_ranks(
        self, power_system_id: EntityId, reader_chapter: int
    ) -> list[Rank]:
        models = (
            self.session.query(RankModel)
            .filter(
                RankModel.power_system_id == power_system_id.value,
                RankModel.introduced_chapter <= reader_chapter,
            )
            .all()
        )
        return [self._to_domain(m) for m in models]

    def save(self, rank: Rank) -> None:
        model = self.session.query(RankModel).filter_by(id=rank.id.value).first()
        if not model:
            model = RankModel(id=rank.id.value)
            self.session.add(model)

        model.power_system_id = rank.power_system_id.value
        model.name = rank.name
        model.slug = rank.slug
        model.order = rank.order
        model.introduced_chapter = rank.introduced_chapter.value
        model.description = rank.description
        model.parent_rank_id = (
            rank.parent_rank_id.value if rank.parent_rank_id else None
        )
        self.session.flush()
