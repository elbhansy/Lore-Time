import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from packages.domain.events.event_query import EventQuery
from packages.domain.services.event_query_service import EventQueryService
from packages.domain.value_objects.event_type import EventType

from ....repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from ...application.events.query_events import QueryEventsUseCase
from ...application.exceptions import InvalidChapter
from ...application.exceptions import ValidationError as AppValidationError
from ...dependencies.database import get_db
from ...schemas.events import EventQueryResultDTO

router = APIRouter(tags=["Events"])


def get_query_events_uc(db: Session = Depends(get_db)) -> QueryEventsUseCase:
    repo = SQLAlchemyEventRepository(db)
    service = EventQueryService(repo)
    return QueryEventsUseCase(service)


@router.get("/series/{series_id}/events", response_model=EventQueryResultDTO)
def query_events(
    series_id: uuid.UUID,
    reader_chapter: int = Query(..., ge=1),
    from_chapter: int = Query(1, ge=1),
    to_chapter: int | None = Query(None, ge=1),
    type: str | None = Query(None),
    subject_id: str | None = Query(None),
    target_id: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    use_case: QueryEventsUseCase = Depends(get_query_events_uc),
):
    types = []
    if type:
        try:
            types = [EventType(type)]
        except ValueError:
            raise AppValidationError("Invalid event type")

    try:
        query = EventQuery(
            series_id=str(series_id),
            reader_chapter=reader_chapter,
            from_chapter=from_chapter,
            to_chapter=to_chapter,
            event_types=types,
            subject_id=subject_id,
            target_id=target_id,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        # e.g., to_chapter > reader_chapter
        raise InvalidChapter(str(e))

    result = use_case.execute(query)

    return {
        "reader_chapter": result.reader_chapter,
        "from_chapter": result.from_chapter,
        "to_chapter": result.to_chapter,
        "items": [
            {
                "id": str(evt.id.value),
                "series_id": str(evt.series_id.value),
                "chapter_id": str(evt.chapter_id.value),
                "sequence": evt.sequence,
                "type": evt.type.value,
                "subject_type": evt.subject_type.value,
                "subject_id": str(evt.subject_id.value),
                "target_type": evt.target_type.value if evt.target_type else None,
                "target_id": str(evt.target_id.value) if evt.target_id else None,
                "previous_state": evt.previous_state,
                "new_state": evt.new_state,
                "metadata": evt.metadata,
            }
            for evt in result.items
        ],
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "has_next": result.has_next,
    }
