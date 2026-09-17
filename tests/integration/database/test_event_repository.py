import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.repositories.sqlalchemy_chapter_repository import (
    SQLAlchemyChapterRepository,
)
from apps.api.repositories.sqlalchemy_character_repository import (
    SQLAlchemyCharacterRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import SQLAlchemyEventRepository
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
)
from infrastructure.database.models import Base
from packages.domain.entities.chapter import Chapter
from packages.domain.entities.character import Character
from packages.domain.entities.event import Event
from packages.domain.entities.series import Series
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId
from packages.domain.value_objects.entity_type import EntityType
from packages.domain.value_objects.event_type import EventType

# Real PostgreSQL Integration Testing
DATABASE_URL = (
    "postgresql+psycopg://timeline_user:timeline_password@localhost:5432/timeline_db"
)

import uuid


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(engine):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


def test_event_polymorphic_mapping(db_session):
    # Setup repos
    series_repo = SQLAlchemySeriesRepository(db_session)
    chapter_repo = SQLAlchemyChapterRepository(db_session)
    char_repo = SQLAlchemyCharacterRepository(db_session)
    event_repo = SQLAlchemyEventRepository(db_session)

    # 1. Create Series
    sid = uuid.uuid4()
    series = Series(
        id=EntityId(sid),
        title="Test Series",
        slug=f"test-series-{str(sid)[:8]}",
        total_chapters=100,
    )
    series_repo.save(series)

    # 2. Create Chapter 100
    chapter = Chapter(
        id=EntityId.generate(),
        series_id=series.id,
        number=ChapterNumber(100),
        title="Climax",
    )
    chapter_repo.save(chapter)

    # 3. Create Character A
    char_a = Character(
        id=EntityId.generate(), series_id=series.id, name="Character A", description=""
    )
    char_repo.save(char_a)

    db_session.commit()

    # 4. Create Event (POWER_RANK_CHANGED)
    event = Event(
        id=EntityId.generate(),
        series_id=series.id,
        chapter_id=chapter.id,
        sequence=1,
        type=EventType.POWER_RANK_CHANGED,
        subject_type=EntityType.CHARACTER,
        subject_id=char_a.id,
        previous_state={"rank": "B"},
        new_state={"rank": "A"},
    )
    event_repo.save(event)
    db_session.commit()

    # 5. Read back and verify mapping (SQLAlchemy -> Domain)
    retrieved_event = event_repo.get(event.id)
    assert isinstance(retrieved_event, Event)  # Ensure it's a Domain Event
    assert retrieved_event.id == event.id
    assert retrieved_event.type == EventType.POWER_RANK_CHANGED
    assert retrieved_event.subject_type == EntityType.CHARACTER
    assert retrieved_event.subject_id == char_a.id
    assert retrieved_event.new_state == {"rank": "A"}
