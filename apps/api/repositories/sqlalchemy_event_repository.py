from sqlalchemy.orm import Session, joinedload

from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from packages.domain.entities.event import Event
from packages.domain.events.event_query import EventQuery
from packages.domain.repositories.event_repository import EventRepository
from packages.domain.services.event_ordering import EventEnvelope
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType


class SQLAlchemyEventRepository(EventRepository):
    def __init__(self, session: Session):
        self.session = session

    def _to_domain(self, model: EventModel) -> Event:
        target_id = EntityId(model.target_id) if model.target_id else None
        target_type = EntityType(model.target_type) if model.target_type else None

        return Event(
            id=EntityId(model.id),
            series_id=EntityId(model.series_id),
            chapter_id=EntityId(model.chapter_id),
            sequence=model.sequence,
            type=EventType(model.type),
            subject_type=EntityType(model.subject_type),
            subject_id=EntityId(model.subject_id),
            target_type=target_type,
            target_id=target_id,
            previous_state=model.previous_state or {},
            new_state=model.new_state or {},
            metadata=model.metadata_ or {},
        )

    def _to_envelope(self, model: EventModel) -> EventEnvelope:
        event = self._to_domain(model)
        chapter_number = (
            ChapterNumber(model.chapter.number) if model.chapter else ChapterNumber(1)
        )
        return EventEnvelope(event=event, chapter_number=chapter_number)

    def get(self, id: EntityId) -> Event | None:
        model = self.session.query(EventModel).filter_by(id=id.value).first()
        if not model:
            return None
        return self._to_domain(model)

    def get_by_chapter(
        self, series_id: EntityId, chapter_number: ChapterNumber
    ) -> list[EventEnvelope]:
        models = (
            self.session.query(EventModel)
            .options(joinedload(EventModel.chapter))
            .join(EventModel.chapter)
            .filter(
                EventModel.series_id == series_id.value,
                ChapterModel.number == chapter_number.value,
            )
            .all()
        )
        return [self._to_envelope(m) for m in models]

    def get_by_chapter_range(
        self,
        series_id: EntityId,
        from_chapter: ChapterNumber,
        to_chapter: ChapterNumber,
    ) -> list[EventEnvelope]:
        models = (
            self.session.query(EventModel)
            .options(joinedload(EventModel.chapter))
            .join(EventModel.chapter)
            .filter(
                EventModel.series_id == series_id.value,
                ChapterModel.number >= from_chapter.value,
                ChapterModel.number <= to_chapter.value,
            )
            .order_by(
                ChapterModel.number.asc(),
                EventModel.sequence.asc(),
                EventModel.id.asc(),
            )
            .all()
        )
        return [self._to_envelope(m) for m in models]

    def get_all_by_series(
        self, series_id: EntityId, to_chapter: ChapterNumber | None = None
    ) -> list[EventEnvelope]:
        query = (
            self.session.query(EventModel)
            .options(joinedload(EventModel.chapter))
            .join(EventModel.chapter)
            .filter(EventModel.series_id == series_id.value)
        )
        if to_chapter is not None:
            query = query.filter(ChapterModel.number <= to_chapter.value)

        models = query.order_by(
            ChapterModel.number.asc(), EventModel.sequence.asc(), EventModel.id.asc()
        ).all()
        return [self._to_envelope(m) for m in models]

    def _build_base_query(self, q: EventQuery):
        query = (
            self.session.query(EventModel)
            .join(EventModel.chapter)
            .filter(EventModel.series_id == q.series_id)
        )

        # PostgreSQL filtering
        if q.from_chapter:
            query = query.filter(ChapterModel.number >= q.from_chapter)
        if q.to_chapter:
            query = query.filter(ChapterModel.number <= q.to_chapter)

        if q.event_types:
            query = query.filter(EventModel.type.in_([t.value for t in q.event_types]))

        if q.subject_id:
            query = query.filter(EventModel.subject_id == q.subject_id)

        if q.target_id:
            query = query.filter(EventModel.target_id == q.target_id)

        return query

    def query(self, q: EventQuery) -> list[Event]:
        # Sort deterministic: chapter_number -> sequence -> event_id
        # Pagination is applied here after filtering.
        query = self._build_base_query(q)
        query = query.order_by(
            ChapterModel.number.asc(), EventModel.sequence.asc(), EventModel.id.asc()
        )

        offset = (q.page - 1) * q.page_size
        query = query.offset(offset).limit(q.page_size)

        models = query.all()
        return [self._to_domain(m) for m in models]

    def count(self, q: EventQuery) -> int:
        return self._build_base_query(q).count()

    def save(self, event: Event) -> None:
        model = self.session.query(EventModel).filter_by(id=event.id.value).first()
        if not model:
            model = EventModel(id=event.id.value)
            self.session.add(model)

        model.series_id = event.series_id.value
        model.chapter_id = event.chapter_id.value
        model.sequence = event.sequence
        model.type = event.type.value
        model.subject_type = event.subject_type.value
        model.subject_id = event.subject_id.value

        if event.target_type:
            model.target_type = event.target_type.value
        if event.target_id:
            model.target_id = event.target_id.value

        model.previous_state = event.previous_state
        model.new_state = event.new_state
        model.metadata_ = event.metadata
