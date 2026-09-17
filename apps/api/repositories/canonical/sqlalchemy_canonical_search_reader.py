from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from packages.domain.canonical.queries.canonical_event_dto import CanonicalEventDTO
from packages.domain.canonical.queries.paginated_response import PaginatedResponse
from packages.domain.canonical.search.canonical_search_query import CanonicalSearchQuery
from packages.domain.canonical.search.canonical_search_reader import (
    CanonicalSearchReader,
)


class SQLAlchemyCanonicalSearchReader(CanonicalSearchReader):
    def __init__(self, session: Session):
        self.session = session

    def search_events(
        self, query: CanonicalSearchQuery
    ) -> PaginatedResponse[CanonicalEventDTO]:
        # Start constructing the query
        stmt = select(EventModel, ChapterModel.number).join(
            ChapterModel, EventModel.chapter_id == ChapterModel.id
        )

        # Structured Filters (Exact Matches)
        stmt = stmt.where(EventModel.series_id == query.series_id)
        if query.chapter_id:
            stmt = stmt.where(EventModel.chapter_id == query.chapter_id)
        if query.event_type:
            stmt = stmt.where(EventModel.type == query.event_type)
        if query.subject_id:
            stmt = stmt.where(EventModel.subject_id == query.subject_id)
        if query.target_id:
            stmt = stmt.where(EventModel.target_id == query.target_id)

        # Full Text Search
        has_query = bool(query.q and query.q.strip())
        if has_query:
            # We use Postgres' native plainto_tsquery for simple user text queries
            ts_query = func.plainto_tsquery("english", query.q)
            stmt = stmt.where(EventModel.search_vector.op("@@")(ts_query))

        # Total count query before pagination
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = self.session.execute(count_stmt).scalar() or 0

        # Deterministic Ordering
        # rank -> chapter_number -> sequence -> event_id
        if has_query:
            ts_rank = func.ts_rank(EventModel.search_vector, ts_query)
            stmt = stmt.order_by(
                desc(ts_rank),
                asc(ChapterModel.number),
                asc(EventModel.sequence),
                asc(EventModel.id),
            )
        else:
            stmt = stmt.order_by(
                asc(ChapterModel.number), asc(EventModel.sequence), asc(EventModel.id)
            )

        # Pagination (Basic Offset/Limit for M2.7)
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
                published_at=event.created_at,
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
