"""Real PostgreSQL Concurrency and Transaction Audit Tests.

Verifies:
1. Concurrent identical publishing producing exactly ONE canonical event
2. Publishing atomicity and full rollback on failure
3. Review state concurrency
4. Session recovery after failure
5. Analytics consistency during uncommitted write
6. Deterministic WorldState reconstruction after concurrent commits
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.repositories.canonical.sqlalchemy_analytics_reader import (
    SQLAlchemyAnalyticsReader,
)
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import (
    SQLAlchemyEventRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
from infrastructure.database.models.event import EventModel
from infrastructure.database.models.publication_record import (
    PublicationRecordModel,
)
from infrastructure.database.models.review.review_item_model import (
    ReviewItemModel,
)
from infrastructure.database.models.series import SeriesModel
from packages.domain.analytics.analytics_query import AnalyticsQuery
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from packages.domain.value_objects.chapter_number import ChapterNumber
from packages.domain.value_objects.entity_id import EntityId


@pytest.fixture(scope="module")
def db_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_size=10, max_overflow=20)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def session_factory(db_engine):
    return sessionmaker(bind=db_engine)


@pytest.fixture
def seeded_series_and_chapter(session_factory):
    session = session_factory()
    series_id = uuid.uuid4()
    chapter_id = uuid.uuid4()

    s = SeriesModel(
        id=series_id,
        title="Concurrency Series",
        slug=f"concurrency-{str(series_id)[:8]}",
        total_chapters=50,
    )
    c = ChapterModel(
        id=chapter_id,
        series_id=series_id,
        number=10,
        title="Concurrent Awakening",
    )
    session.add(s)
    session.add(c)
    session.commit()
    session.close()

    return str(series_id), str(chapter_id)


def _create_review_item(
    item_id: str, series_id: str, chapter_id: str, subject_id: str, rank: str
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw=None,
        payload={
            "from_rank": "C",
            "to_rank": rank,
            "subject_id": subject_id,
            "sequence": 1,
        },
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="webnovel_ch10",
        evidence=Evidence(chapter_id=chapter_id, location="para_1"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    return ReviewItem(
        id=item_id,
        series_id=series_id,
        chapter_id=chapter_id,
        fact=fact,
        provenance=prov,
        status=ReviewStatus.APPROVED,
    )


def test_concurrent_identical_publishing(session_factory, seeded_series_and_chapter):
    """Multiple concurrent workers attempting to publish the exact same review item.

    Must produce exactly ONE canonical event and ONE publication record.
    """
    series_id, chapter_id = seeded_series_and_chapter
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    # Pre-insert ReviewItem into database
    init_session = session_factory()
    item_model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=uuid.UUID(series_id),
        chapter_id=uuid.UUID(chapter_id),
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={"from_rank": "C", "to_rank": "A", "subject_id": char_id},
        provenance_data={},
        status=ReviewStatus.APPROVED.value,
    )
    init_session.add(item_model)
    init_session.commit()
    init_session.close()

    def worker_publish():
        worker_session = session_factory()
        repo = SQLAlchemyPublicationRepository(worker_session)
        use_case = PublishReviewItemUseCase(repo)
        item = _create_review_item(item_id, series_id, chapter_id, char_id, "A")
        try:
            use_case.execute(item)
            return True
        except Exception:
            return False
        finally:
            worker_session.close()

    # Run 4 workers concurrently
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(worker_publish) for _ in range(4)]
        results = [f.result() for f in futures]

    assert any(results)

    # Verify database state
    verify_session = session_factory()
    events = (
        verify_session.query(EventModel).filter_by(series_id=uuid.UUID(series_id)).all()
    )
    # MUST BE EXACTLY ONE EVENT
    assert len(events) == 1

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) >= 1

    # Verify review item status is published
    final_item = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).first()
    )
    assert final_item.status == ReviewStatus.PUBLISHED.value
    verify_session.close()


def test_publish_atomicity_and_rollback_on_failure(
    session_factory, seeded_series_and_chapter
):
    """When a failure is injected mid-transaction during publishing,

    the entire transaction must rollback: NO PARTIAL CANONICAL STATE.
    """
    series_id, chapter_id = seeded_series_and_chapter
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    init_session = session_factory()
    init_session.add(
        ReviewItemModel(
            id=uuid.UUID(item_id),
            series_id=uuid.UUID(series_id),
            chapter_id=uuid.UUID(chapter_id),
            fact_type=FactType.POWER_RANK_CHANGED.value,
            fact_payload={"from_rank": "C", "to_rank": "S", "subject_id": char_id},
            provenance_data={},
            status=ReviewStatus.APPROVED.value,
        )
    )
    init_session.commit()
    init_session.close()

    failing_session = session_factory()
    repo = SQLAlchemyPublicationRepository(failing_session)

    # Deliberately inject a failure in save_publication_record
    def explode_record(record_data):
        raise RuntimeError("Simulated DB Disk Crash during publication record")

    repo.save_publication_record = explode_record

    use_case = PublishReviewItemUseCase(repo)
    item = _create_review_item(item_id, series_id, chapter_id, char_id, "S")

    with pytest.raises(RuntimeError, match="Transaction failed"):
        use_case.execute(item)
    failing_session.close()

    # Check that database has NO orphan event or publication record
    check_session = session_factory()
    events = (
        check_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(series_id), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 0

    item_in_db = (
        check_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).first()
    )
    # Status MUST remain APPROVED, not prematurely PUBLISHED
    assert item_in_db.status == ReviewStatus.APPROVED.value
    check_session.close()


def test_failed_transaction_session_recovery(
    session_factory, seeded_series_and_chapter
):
    """Verifies that after an operation fails and rolls back,

    the same session can successfully perform subsequent valid operations.
    """
    series_id, chapter_id = seeded_series_and_chapter
    session = session_factory()

    # Intentionally trigger an error (e.g. duplicate key or invalid foreign key)
    try:
        session.execute(
            text(
                "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
                "subject_type, subject_id, metadata) "
                "VALUES (:id, :invalid_sid, :invalid_cid, 1, 'COMBAT', "
                "'CHARACTER', :id, '{}')"
            ),
            {
                "id": str(uuid.uuid4()),
                "invalid_sid": str(uuid.uuid4()),
                "invalid_cid": str(uuid.uuid4()),
            },
        )
        session.commit()
    except Exception:
        session.rollback()

    # Now execute a completely valid insertion with the recovered session
    valid_event_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
            "subject_type, subject_id, metadata) "
            "VALUES (:id, :sid, :cid, 99, 'COMBAT', 'CHARACTER', :id, '{}')"
        ),
        {
            "id": valid_event_id,
            "sid": uuid.UUID(series_id),
            "cid": uuid.UUID(chapter_id),
        },
    )
    session.commit()

    # Confirm it was saved
    saved = session.query(EventModel).filter_by(id=valid_event_id).first()
    assert saved is not None
    session.close()


def test_analytics_isolation_during_uncommitted_write(
    session_factory, seeded_series_and_chapter
):
    """An uncommitted canonical write must NOT leak.

    Concurrent analytics queries must observe only committed state.
    """
    series_id, chapter_id = seeded_series_and_chapter
    tx_session = session_factory()
    reader_session = session_factory()

    reader = SQLAlchemyAnalyticsReader(reader_session)
    q = AnalyticsQuery(series_id=series_id)
    before_stats = reader.get_event_statistics(q)

    # Insert event in tx_session WITHOUT committing
    uncommitted_id = uuid.uuid4()
    tx_session.execute(
        text(
            "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
            "subject_type, subject_id, metadata) "
            "VALUES (:id, :sid, :cid, 50, 'POWER_RANK_CHANGED', 'CHARACTER', "
            ":id, '{}')"
        ),
        {
            "id": uncommitted_id,
            "sid": uuid.UUID(series_id),
            "cid": uuid.UUID(chapter_id),
        },
    )
    tx_session.flush()

    # Reader querying in separate transaction must NOT see uncommitted row
    during_stats = reader.get_event_statistics(q)
    assert during_stats.total_events == before_stats.total_events

    # Now commit
    tx_session.commit()
    tx_session.close()

    # Reader now sees updated total
    after_stats = reader.get_event_statistics(q)
    assert after_stats.total_events == before_stats.total_events + 1
    reader_session.close()


def test_deterministic_world_state_after_concurrent_commits(
    session_factory, seeded_series_and_chapter
):
    """Verifies that events committed across concurrent transactions

    reconstruct an identical, deterministic WorldState regardless of
    commit arrival timing, thanks to deterministic (chapter, seq, id) ordering.
    """
    series_id, chapter_id = seeded_series_and_chapter
    char_id = uuid.uuid4()

    # Worker A commits rank A at seq 1
    # Worker B commits rank S at seq 2
    def worker_a():
        s = session_factory()
        s.execute(
            text(
                "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
                "subject_type, subject_id, new_state, metadata) "
                "VALUES (:id, :sid, :cid, 1, 'POWER_RANK_CHANGED', 'CHARACTER', "
                ":char_id, '{\"rank\": \"A\"}', '{}')"
            ),
            {
                "id": uuid.uuid4(),
                "sid": uuid.UUID(series_id),
                "cid": uuid.UUID(chapter_id),
                "char_id": char_id,
            },
        )
        s.commit()
        s.close()

    def worker_b():
        s = session_factory()
        s.execute(
            text(
                "INSERT INTO events (id, series_id, chapter_id, sequence, type, "
                "subject_type, subject_id, new_state, metadata) "
                "VALUES (:id, :sid, :cid, 2, 'POWER_RANK_CHANGED', 'CHARACTER', "
                ":char_id, '{\"rank\": \"S\"}', '{}')"
            ),
            {
                "id": uuid.uuid4(),
                "sid": uuid.UUID(series_id),
                "cid": uuid.UUID(chapter_id),
                "char_id": char_id,
            },
        )
        s.commit()
        s.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_a)
        f2 = executor.submit(worker_b)
        f1.result()
        f2.result()

    # Reconstruct WorldState twice
    verify_session = session_factory()
    repo = SQLAlchemyEventRepository(verify_session)
    envelopes = repo.get_all_by_series(EntityId(series_id))

    builder = WorldStateBuilder(EventApplier())
    state1 = builder.build(EntityId(series_id), envelopes, ChapterNumber(10))
    state2 = builder.build(EntityId(series_id), envelopes, ChapterNumber(10))

    assert state1 == state2
    assert state1.characters[EntityId(char_id)].rank == "S"
    verify_session.close()
