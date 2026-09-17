"""Phase 4.3 Query Performance and Temporal Boundary Regression Tests."""

import uuid

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.timeline.get_timeline_events import (
    GetTimelineEventsUseCase,
)
from apps.api.app.application.timeline.get_world_state import GetWorldStateUseCase
from apps.api.app.config import get_settings
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.series import SeriesModel
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.event_type import EventType


@pytest.fixture(scope="module")
def audit_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def audit_session(audit_engine):
    Session = sessionmaker(bind=audit_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_timeline_query_pushdown_semantics(audit_session):
    """Verifies that GetTimelineEventsUseCase pushdown returns the exact same logical

    events in the exact same deterministic order as loading and sorting in Python.
    """
    sid = uuid.uuid4()
    audit_session.add(
        SeriesModel(
            id=sid,
            title="Pushdown Series",
            slug=f"pd-{str(sid)[:8]}",
            total_chapters=10,
        )
    )
    cids = [uuid.uuid4() for _ in range(5)]
    for i, cid in enumerate(cids):
        audit_session.add(
            ChapterModel(id=cid, series_id=sid, number=i + 1, title=f"Ch {i + 1}")
        )

    # 20 events: 4 per chapter
    for i in range(20):
        chap_idx = i // 4
        audit_session.add(
            EventModel(
                id=uuid.uuid4(),
                series_id=sid,
                chapter_id=cids[chap_idx],
                sequence=i % 4,
                type=EventType.POWER_RANK_CHANGED.value,
                subject_type="CHARACTER",
                subject_id=uuid.uuid4(),
                metadata_={},
                new_state={},
            )
        )
    audit_session.commit()

    series_repo = SQLAlchemySeriesRepository(audit_session)
    event_repo = SQLAlchemyEventRepository(audit_session)
    use_case = GetTimelineEventsUseCase(series_repo, event_repo)

    # Request range chapter 2 to 4 with reader_chapter 4
    results = use_case.execute(
        series_id=sid, reader_chapter=4, from_chapter=2, to_chapter=4
    )

    # Chapters 2, 3, 4 should have 4 * 3 = 12 events
    assert len(results) == 12
    # Verify strict range
    for env in results:
        assert 2 <= env.chapter_number.value <= 4

    # Verify deterministic ordering: chapter ASC -> sequence ASC -> id ASC
    for i in range(len(results) - 1):
        curr = (
            results[i].chapter_number.value,
            results[i].event.sequence,
            str(results[i].event.id.value),
        )
        nxt = (
            results[i + 1].chapter_number.value,
            results[i + 1].event.sequence,
            str(results[i + 1].event.id.value),
        )
        assert curr < nxt


def test_worldstate_temporal_boundary_never_loads_future_events(audit_session):
    """Verifies that WorldState reconstruction NEVER loads future events into memory."""
    sid = uuid.uuid4()
    audit_session.add(
        SeriesModel(
            id=sid, title="WS Series", slug=f"ws-{str(sid)[:8]}", total_chapters=5
        )
    )
    c1, c2, c3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    audit_session.add(ChapterModel(id=c1, series_id=sid, number=1, title="Ch 1"))
    audit_session.add(ChapterModel(id=c2, series_id=sid, number=2, title="Ch 2"))
    audit_session.add(ChapterModel(id=c3, series_id=sid, number=3, title="Ch 3"))

    char_id = uuid.uuid4()
    # Event at ch 1: Character created
    audit_session.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c1,
            sequence=0,
            type=EventType.CHARACTER_INTRODUCED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"name": "Hero"},
        )
    )
    # Event at ch 2: Power rank up
    audit_session.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c2,
            sequence=0,
            type=EventType.POWER_RANK_CHANGED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"rank": "Tier 2"},
        )
    )
    # Event at ch 3: Future event (Spoiler!)
    future_event_id = uuid.uuid4()
    audit_session.add(
        EventModel(
            id=future_event_id,
            series_id=sid,
            chapter_id=c3,
            sequence=0,
            type=EventType.POWER_RANK_CHANGED.value,
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"rank": "Tier 3"},
        )
    )
    audit_session.commit()

    series_repo = SQLAlchemySeriesRepository(audit_session)
    event_repo = SQLAlchemyEventRepository(audit_session)
    builder = WorldStateBuilder(EventApplier())
    use_case = GetWorldStateUseCase(series_repo, event_repo, builder)

    # Build world state at chapter 2 (reader_chapter=2)
    ws = use_case.execute(series_id=sid, reader_chapter=2)

    # Invariant: Future event from chapter 3 is not applied
    char_state = ws.characters.get(EntityId(char_id))
    assert char_state is not None
    assert char_state.rank == "Tier 2"  # NOT Tier 3!

    # Direct repository check: get_all_by_series with to_chapter=2 should NOT load chapter 3
    loaded = event_repo.get_all_by_series(EntityId(sid), to_chapter=ChapterNumber(2))
    assert len(loaded) == 2
    assert all(env.chapter_number.value <= 2 for env in loaded)
    assert not any(env.event.id.value == future_event_id for env in loaded)
