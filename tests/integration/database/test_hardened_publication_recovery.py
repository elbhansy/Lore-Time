"""Hardened Publication Recovery Tests (COMMAND 07).

Audits and verifies:
- PublishReviewItemUseCase
- Publication fingerprint determinism and deduplication
- Database unique constraints
- ON CONFLICT DO NOTHING behavior
- Transaction ownership and atomicity
- Canonical event creation

Tests:
1. First publication
2. Duplicate publication (sequential)
3. Duplicate concurrent publication (race condition with multiple workers)
4. Failure before commit (validation or preparation failure)
5. Failure after mutation but before commit (mid-transaction crash / rollback)
6. Retry after failure (recovery and subsequent success)
7. Timeout followed by retry (client-side timeout / unknown outcome)

Guarantees Verified:
- ONE logical publication
- ONE canonical event
- NO partial state
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
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
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.publishing.canonical_publisher import (
    PublicationDomainError,
)
from packages.domain.publishing.publication_status import PublicationStatus
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def pub_engine():
    """Live PostgreSQL engine."""
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def pub_session_factory(pub_engine):
    """Factory returning isolated Sessions."""
    return sessionmaker(bind=pub_engine)


@pytest.fixture
def series_context(pub_session_factory):
    """Creates a distinct series and chapter context in PostgreSQL."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    Session = pub_session_factory()
    series = SeriesModel(
        id=sid,
        title="Publication Hardening Series",
        slug=f"pub-hard-{sid.hex[:8]}",
        total_chapters=20,
    )
    chapter = ChapterModel(
        id=cid,
        series_id=sid,
        number=1,
        title="Chapter 1",
    )
    Session.add(series)
    Session.add(chapter)
    Session.commit()
    Session.close()
    return str(sid), str(cid)


def _create_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "A",
    status: ReviewStatus = ReviewStatus.APPROVED,
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw="Rival" if target_id else None,
        payload={
            "from_rank": "D",
            "to_rank": rank,
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        extraction_confidence=0.95,
        evidence=RawFactEvidence(location="para_1"),
    )
    prov = Provenance(
        source_id="webnovel_ch1",
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
        status=status,
    )


def _seed_review_item_in_db(
    pub_session_factory,
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "A",
    status: ReviewStatus = ReviewStatus.APPROVED,
):
    Session = pub_session_factory()
    model = ReviewItemModel(
        id=uuid.UUID(item_id),
        series_id=uuid.UUID(series_id),
        chapter_id=uuid.UUID(chapter_id),
        fact_type=FactType.POWER_RANK_CHANGED.value,
        fact_payload={
            "from_rank": "D",
            "to_rank": rank,
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        provenance_data={"source": "test_hardening"},
        status=status.value,
    )
    Session.add(model)
    Session.commit()
    Session.close()


# ==============================================================================
# 1. FIRST PUBLICATION
# ==============================================================================


def test_first_publication_creates_single_canonical_event_and_publication_record(
    pub_session_factory, series_context
):
    """First publication of an approved review item:

    - Atomically creates exactly ONE canonical event
    - Creates exactly ONE publication record
    - Transitions ReviewItem status to PUBLISHED
    - Creates canonical entity and relationship records
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())

    _seed_review_item_in_db(
        pub_session_factory, item_id, sid, cid, char_id, target_id=target_id
    )

    session = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(session)
    use_case = PublishReviewItemUseCase(repo)
    item = _create_review_item(item_id, sid, cid, char_id, target_id=target_id)

    use_case.execute(item)
    assert item.status == ReviewStatus.PUBLISHED
    session.close()

    # Verify canonical store
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 1
    assert events[0].type == FactType.POWER_RANK_CHANGED.value

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 1
    assert records[0].status == PublicationStatus.PUBLISHED.value

    db_item = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert db_item.status == ReviewStatus.PUBLISHED.value

    verify_session.close()


# ==============================================================================
# 2. DUPLICATE PUBLICATION (SEQUENTIAL RETRY)
# ==============================================================================


def test_duplicate_publication_sequential_is_idempotent_no_op(
    pub_session_factory, series_context
):
    """Calling PublishReviewItemUseCase sequentially on an already published item:

    - Produces NO duplicate canonical events
    - Produces NO duplicate publication records
    - Retains single logical effect
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)

    session1 = pub_session_factory()
    use_case1 = PublishReviewItemUseCase(SQLAlchemyPublicationRepository(session1))
    item1 = _create_review_item(item_id, sid, cid, char_id)
    use_case1.execute(item1)
    session1.close()

    # Duplicate call 1: with same domain object (already in PUBLISHED state in memory)
    session2 = pub_session_factory()
    use_case2 = PublishReviewItemUseCase(SQLAlchemyPublicationRepository(session2))
    use_case2.execute(item1)
    session2.close()

    # Duplicate call 2: with fresh domain object (simulating new request from client)
    session3 = pub_session_factory()
    use_case3 = PublishReviewItemUseCase(SQLAlchemyPublicationRepository(session3))
    item_retry = _create_review_item(item_id, sid, cid, char_id)
    use_case3.execute(item_retry)
    session3.close()

    # Assert exactly ONE canonical event and publication record
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 1

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 1
    verify_session.close()


# ==============================================================================
# 3. DUPLICATE CONCURRENT PUBLICATION (RACE CONDITION)
# ==============================================================================


def test_duplicate_concurrent_publication_produces_single_canonical_event(
    pub_session_factory, series_context
):
    """Multiple concurrent workers racing to publish the exact same review item:

    - Row locking (SELECT FOR UPDATE) serializes workers
    - Fingerprint unique constraint & ON CONFLICT DO NOTHING ensures single canonical event
    - Exactly ONE canonical event and publication record exists in the end
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)

    def worker_action():
        worker_session = pub_session_factory()
        repo = SQLAlchemyPublicationRepository(worker_session)
        use_case = PublishReviewItemUseCase(repo)
        item = _create_review_item(item_id, sid, cid, char_id)
        try:
            use_case.execute(item)
            return True
        except Exception:
            return False
        finally:
            worker_session.close()

    # Launch 5 concurrent workers
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker_action) for _ in range(5)]
        results = [f.result() for f in futures]

    assert any(results), "At least one worker must succeed"

    # Verify single canonical event
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 1, f"Expected 1 canonical event, found {len(events)}"

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 1, f"Expected 1 publication record, found {len(records)}"

    item_in_db = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert item_in_db.status == ReviewStatus.PUBLISHED.value
    verify_session.close()


# ==============================================================================
# 4. FAILURE BEFORE COMMIT (PREPARATION / DOMAIN ERROR)
# ==============================================================================


def test_failure_before_commit_produces_no_partial_state(
    pub_session_factory, series_context
):
    """Failure during pre-commit preparation (e.g. invalid review status or missing subject_id):

    - Rejects operation before transaction mutation
    - NO canonical events inserted
    - Review item status remains untouched
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    # Seed in PENDING state (not APPROVED)
    _seed_review_item_in_db(
        pub_session_factory, item_id, sid, cid, char_id, status=ReviewStatus.PENDING
    )

    session = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(session)
    use_case = PublishReviewItemUseCase(repo)
    item = _create_review_item(item_id, sid, cid, char_id, status=ReviewStatus.PENDING)

    with pytest.raises(
        PublicationDomainError, match="Cannot publish ReviewItem in state: PENDING"
    ):
        use_case.execute(item)
    session.close()

    # Verify no state changes in DB
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 0

    item_in_db = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert item_in_db.status == ReviewStatus.PENDING.value
    verify_session.close()


# ==============================================================================
# 5. FAILURE AFTER MUTATION BUT BEFORE COMMIT (ROLLBACK GUARANTEE)
# ==============================================================================


def test_failure_after_mutation_before_commit_rolls_back_completely(
    pub_session_factory, series_context
):
    """Failure occurs after event insertion and graph projection, but before commit:

    - Atomically rolls back ALL mutations
    - ZERO canonical events exist
    - ZERO publication records exist
    - ReviewItem status remains APPROVED
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)

    session = pub_session_factory()
    repo = SQLAlchemyPublicationRepository(session)

    # Injected crash in update_review_status (last action before commit)
    def explode_status_update(*args, **kwargs):
        raise RuntimeError("Crash right before commit")

    repo.update_review_status = explode_status_update

    use_case = PublishReviewItemUseCase(repo)
    item = _create_review_item(item_id, sid, cid, char_id)

    with pytest.raises(
        RuntimeError, match="Transaction failed: Crash right before commit"
    ):
        use_case.execute(item)
    session.close()

    # Strict check: NO PARTIAL STATE
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 0, "Partial canonical event found after rollback!"

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 0, "Partial publication record found after rollback!"

    item_in_db = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert item_in_db.status == ReviewStatus.APPROVED.value
    verify_session.close()


# ==============================================================================
# 6. RETRY AFTER FAILURE
# ==============================================================================


def test_retry_after_failure_successfully_publishes_single_event(
    pub_session_factory, series_context
):
    """When attempt 1 fails and rolls back, subsequent attempt 2 succeeds:

    - Initial attempt fails mid-operation and leaves zero records
    - Retry succeeds cleanly
    - Exactly ONE canonical event and publication record exists in the end
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)

    # Attempt 1: Injected transient network drop
    session1 = pub_session_factory()
    repo1 = SQLAlchemyPublicationRepository(session1)

    def transient_crash(*args, **kwargs):
        raise RuntimeError("Transient connection severed")

    repo1.save_publication_record = transient_crash
    use_case1 = PublishReviewItemUseCase(repo1)
    item1 = _create_review_item(item_id, sid, cid, char_id)

    with pytest.raises(RuntimeError, match="Transaction failed"):
        use_case1.execute(item1)
    session1.close()

    # Confirm clean slate after failure
    check_session = pub_session_factory()
    assert (
        check_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .count()
        == 0
    )
    check_session.close()

    # Attempt 2: Healthy execution on new session
    session2 = pub_session_factory()
    repo2 = SQLAlchemyPublicationRepository(session2)
    use_case2 = PublishReviewItemUseCase(repo2)
    item2 = _create_review_item(item_id, sid, cid, char_id)

    use_case2.execute(item2)
    assert item2.status == ReviewStatus.PUBLISHED
    session2.close()

    # Confirm success
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 1

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 1
    assert records[0].status == PublicationStatus.PUBLISHED.value

    item_in_db = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert item_in_db.status == ReviewStatus.PUBLISHED.value
    verify_session.close()


# ==============================================================================
# 7. TIMEOUT FOLLOWED BY RETRY (UNKNOWN OUTCOME)
# ==============================================================================


def test_timeout_followed_by_retry_produces_single_canonical_event(
    pub_session_factory, series_context
):
    """Client initiates publication, DB commits, but client experiences socket timeout before response:

    - Attempt 1 commits to DB
    - Client retries operation
    - In-transaction row lock & fingerprint idempotency intercepts retry
    - Exactly ONE canonical event and publication record exists
    - Status remains PUBLISHED
    """
    sid, cid = series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    _seed_review_item_in_db(pub_session_factory, item_id, sid, cid, char_id)

    # Attempt 1: Succeeded in DB, but client timed out
    session1 = pub_session_factory()
    repo1 = SQLAlchemyPublicationRepository(session1)
    use_case1 = PublishReviewItemUseCase(repo1)
    item1 = _create_review_item(item_id, sid, cid, char_id)
    use_case1.execute(item1)
    session1.close()

    # Attempt 2: Client retries because timeout left client in doubt
    session2 = pub_session_factory()
    repo2 = SQLAlchemyPublicationRepository(session2)
    use_case2 = PublishReviewItemUseCase(repo2)
    retry_item = _create_review_item(item_id, sid, cid, char_id)
    use_case2.execute(retry_item)
    assert retry_item.status == ReviewStatus.PUBLISHED
    session2.close()

    # Final Invariant Check
    verify_session = pub_session_factory()
    events = (
        verify_session.query(EventModel)
        .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
        .all()
    )
    assert len(events) == 1, f"Expected 1 event, found {len(events)}"

    records = (
        verify_session.query(PublicationRecordModel)
        .filter_by(review_item_id=uuid.UUID(item_id))
        .all()
    )
    assert len(records) == 1, f"Expected 1 publication record, found {len(records)}"

    item_in_db = (
        verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
    )
    assert item_in_db.status == ReviewStatus.PUBLISHED.value
    verify_session.close()
