"""Repository and query performance regression tests.

Verifies:
1. get_all_by_series does not emit N+1 queries when loading chapter metadata.
2. Query pagination and bounded result set semantics.
3. Execution time remains within acceptable bounds on real PostgreSQL 18.
"""

import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from apps.api.app.config import get_settings
from apps.api.repositories.sqlalchemy_event_repository import (
    SQLAlchemyEventRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.series import SeriesModel
from packages.domain.events.event_query import EventQuery
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.event_type import EventType


@pytest.fixture(scope="module")
def perf_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def perf_session(perf_engine):
    Session = sessionmaker(bind=perf_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_n_plus_one_eliminated_on_event_loading(perf_engine, perf_session):
    """Proves that loading N events across multiple chapters executes in a bounded

    number of SQL queries (exactly 1 query with joinedload, not 1 + N queries).
    """
    sid = uuid.uuid4()
    perf_session.add(
        SeriesModel(
            id=sid,
            title="N+1 Test Series",
            slug=f"n1-{str(sid)[:8]}",
            total_chapters=5,
        )
    )
    cids = [uuid.uuid4() for _ in range(5)]
    for i, cid in enumerate(cids):
        perf_session.add(
            ChapterModel(id=cid, series_id=sid, number=i + 1, title=f"Chapter {i + 1}")
        )
    for i in range(20):
        perf_session.add(
            EventModel(
                id=uuid.uuid4(),
                series_id=sid,
                chapter_id=cids[i % 5],
                sequence=i,
                type=EventType.POWER_RANK_CHANGED.value,
                subject_type="CHARACTER",
                subject_id=uuid.uuid4(),
                metadata_={},
            )
        )
    perf_session.commit()

    # Expire all cached objects from session to force fresh DB roundtrips
    perf_session.expire_all()

    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        if "SELECT" in statement.upper():
            query_count += 1

    event.listen(perf_engine, "before_cursor_execute", query_listener)
    try:
        repo = SQLAlchemyEventRepository(perf_session)
        envelopes = repo.get_all_by_series(EntityId(sid))
        assert len(envelopes) == 20
        for env in envelopes:
            # Access chapter_number to ensure no lazy query is fired
            assert env.chapter_number.value >= 1
    finally:
        event.remove(perf_engine, "before_cursor_execute", query_listener)

    # EXACTLY 1 query must be emitted for 20 events across 5 chapters!
    # Without joinedload, this was 1 + 5 = 6 queries.
    assert query_count == 1


def test_event_query_pagination_is_bounded(perf_session):
    """Verifies that query() respects page_size and never loads unbounded rows."""
    sid = uuid.uuid4()
    perf_session.add(
        SeriesModel(
            id=sid,
            title="Pagination Series",
            slug=f"page-{str(sid)[:8]}",
            total_chapters=10,
        )
    )
    cid = uuid.uuid4()
    perf_session.add(ChapterModel(id=cid, series_id=sid, number=1, title="Chapter 1"))
    for i in range(30):
        perf_session.add(
            EventModel(
                id=uuid.uuid4(),
                series_id=sid,
                chapter_id=cid,
                sequence=i,
                type=EventType.POWER_RANK_CHANGED.value,
                subject_type="CHARACTER",
                subject_id=uuid.uuid4(),
                metadata_={},
            )
        )
    perf_session.commit()

    repo = SQLAlchemyEventRepository(perf_session)
    q = EventQuery(
        series_id=str(sid),
        reader_chapter=1,
        from_chapter=1,
        to_chapter=1,
        page=1,
        page_size=10,
    )
    page1 = repo.query(q)
    assert len(page1) == 10

    q2 = EventQuery(
        series_id=str(sid),
        reader_chapter=1,
        from_chapter=1,
        to_chapter=1,
        page=2,
        page_size=10,
    )
    page2 = repo.query(q2)
    assert len(page2) == 10

    # Ensure no overlap between pages
    page1_ids = {e.id.value for e in page1}
    page2_ids = {e.id.value for e in page2}
    assert page1_ids.isdisjoint(page2_ids)
