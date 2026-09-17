from sqlalchemy import asc, func, select
from sqlalchemy.orm import Session

from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.canonical_event_query import CanonicalEventQuery
from packages.domain.canonical.queries.canonical_event_reader import (
    CanonicalEventReader,
)
from packages.domain.canonical.queries.paginated_response import PaginatedResponse


class SQLAlchemyCanonicalEventReader(CanonicalEventReader):
    def __init__(self, session: Session):
        self.session = session

    def get_timeline(
        self, query: CanonicalEventQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        # Start constructing the query, explicitly joining Chapter for ordering
        stmt = select(EventModel, ChapterModel.number).join(
            ChapterModel, EventModel.chapter_id == ChapterModel.id
        )

        # Filters
        stmt = stmt.where(EventModel.series_id == query.series_id)
        if query.chapter_id:
            stmt = stmt.where(EventModel.chapter_id == query.chapter_id)
        if query.event_type:
            stmt = stmt.where(EventModel.type == query.event_type)
        if query.subject_id:
            stmt = stmt.where(EventModel.subject_id == query.subject_id)
        if query.target_id:
            stmt = stmt.where(EventModel.target_id == query.target_id)

        # Total count query before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Deterministic Ordering: chapter_number -> sequence -> event.id
        stmt = stmt.order_by(
            asc(ChapterModel.number), asc(EventModel.sequence), asc(EventModel.id)
        )

        # Pagination
        offset = (query.page - 1) * query.limit
        stmt = stmt.offset(offset).limit(query.limit)

        results = self.session.execute(stmt).all()

        # Convert to DTO
        dtos = []
        for event, chapter_number in results:
            dto = CanonicalEventDTO(
                id=str(event.id),
                series_id=str(event.series_id),
                chapter_id=str(event.chapter_id),
                chapter_number=chapter_number,
                type=event.type,
                subject_id=str(event.subject_id),
                target_id=str(event.target_id) if event.target_id else None,
                payload=event.metadata_.get("payload", {}),
                provenance=event.metadata_.get("provenance", {}),
                published_at=event.created_at,  # Assuming published immediately upon creation
            )
            dtos.append(dto)

        has_next = (offset + query.limit) < total

        return PaginatedResponse(
            items=dtos,
            page=query.page,
            limit=query.limit,
            total=total,
            has_next=has_next,
        )
