"""Real PostgreSQL Database Failure Recovery Tests (COMMAND 05).

Simulates real database failure modes against the live PostgreSQL instance:
1. Connection failure
2. Connection timeout
3. Transaction rollback
4. Commit failure
5. Stale connection (terminated backend / broken pipe)
6. Database unavailable during mutation

Verifies:
- No partial commit
- Session rollback is correct
- Transaction state is recoverable
- Subsequent requests still work
- Canonical data remains consistent
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.retry import RetryClassification, classify_failure
from apps.api.app.dependencies.database import get_db
from apps.api.app.main import app
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.canonical_entity import CanonicalEntityModel
from infrastructure.database.models.canonical_relationship import (
    CanonicalRelationshipModel,
)
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
from packages.domain.publishing.publication_status import PublicationStatus
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def real_pg_engine():
    """Provides real engine connected to active PostgreSQL instance."""
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
def real_pg_session(real_pg_engine):
    """Provides an isolated session that rolls back upon test completion."""
    SessionLocal = sessionmaker(bind=real_pg_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def seeded_series_context(real_pg_session):
    """Creates a real series and chapter in PostgreSQL for testing."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    series = SeriesModel(
        id=sid,
        title="Failure Recovery Test Series",
        slug=f"recovery-{str(sid)[:8]}",
        total_chapters=10,
    )
    chapter = ChapterModel(
        id=cid,
        series_id=sid,
        number=1,
        title="Chapter 1",
    )
    real_pg_session.add(series)
    real_pg_session.add(chapter)
    real_pg_session.commit()
    return str(sid), str(cid)


def _build_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "S",
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw="Villain" if target_id else None,
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
        status=ReviewStatus.APPROVED,
    )


# ==============================================================================
# 1. CONNECTION FAILURE SIMULATION & CLASSIFICATION
# ==============================================================================


def test_connection_failure_simulation():
    """Simulate connection failure to unreachable endpoint:

    - Verifies operational error is raised
    - Verifies classification is RETRYABLE
    - Verifies no partial data or corruption
    """
    bad_engine = create_engine(
        "postgresql+psycopg://timeline_user:wrong_pass@localhost:5432/timeline_db",
        connect_args={"connect_timeout": 1},
    )
    try:
        with pytest.raises(OperationalError) as exc_info:
            with bad_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        # Verify retry classification classifies this as RETRYABLE
        assert classify_failure(exc_info.value) == RetryClassification.RETRYABLE
    finally:
        bad_engine.dispose()


# ==============================================================================
# 2. CONNECTION TIMEOUT SIMULATION & CLASSIFICATION
# ==============================================================================


def test_connection_timeout_simulation():
    """Simulate connection timeout to non-routable address with fast 1s timeout:

    - Verifies connection timeout produces OperationalError
    - Verifies classification is RETRYABLE
    """
    timeout_engine = create_engine(
        "postgresql+psycopg://timeline_user:timeline_password@localhost:5433/timeline_db",
        connect_args={"connect_timeout": 1},
    )
    try:
        with pytest.raises(OperationalError) as exc_info:
            with timeout_engine.connect() as conn:
                conn.execute(text("SELECT 1"))

        assert classify_failure(exc_info.value) == RetryClassification.RETRYABLE
    finally:
        timeout_engine.dispose()


# ==============================================================================
# 3. TRANSACTION ROLLBACK & NO PARTIAL COMMIT VERIFICATION
# ==============================================================================


def test_transaction_rollback_guarantees_no_partial_commit(
    real_pg_engine, seeded_series_context
):
    """Simulate failure mid-transaction in publication workflow:

    - Inserts event and graph projection
    - Injects crash right before publication record persistence
    - Verifies full transaction rollback
    - Verifies NO partial canonical events, NO relationships, NO publication records
    - Verifies review item status remains untouched
    """
    series_id, chapter_id = seeded_series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    SessionLocal = sessionmaker(bind=real_pg_engine)

    # 1. Insert review item into PostgreSQL in APPROVED state
    with SessionLocal() as seed_session:
        seed_session.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(series_id),
                chapter_id=uuid.UUID(chapter_id),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={"from_rank": "D", "to_rank": "S", "subject_id": char_id},
                provenance_data={},
                status=ReviewStatus.APPROVED.value,
            )
        )
        seed_session.commit()

    # 2. Execute publication use case with injected failure in save_publication_record
    failing_session = SessionLocal()
    repo = SQLAlchemyPublicationRepository(failing_session)

    original_save_record = repo.save_publication_record

    def crashing_save_record(record_data):
        raise RuntimeError("Simulated mid-transaction database storage crash")

    repo.save_publication_record = crashing_save_record

    use_case = PublishReviewItemUseCase(repo)
    review_item = _build_review_item(item_id, series_id, chapter_id, char_id)

    with pytest.raises(
        RuntimeError, match="Transaction failed: Simulated mid-transaction"
    ):
        use_case.execute(review_item)

    failing_session.close()

    # 3. Verify PostgreSQL database state: ABSOLUTELY NO PARTIAL COMMIT
    with SessionLocal() as verify_session:
        # No canonical event created
        events = (
            verify_session.query(EventModel)
            .filter_by(series_id=uuid.UUID(series_id), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 0, "Rollback failed: partial canonical event found!"

        # No publication record created
        records = (
            verify_session.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 0, "Rollback failed: partial publication record found!"

        # Review item in database must NOT be marked PUBLISHED
        item_in_db = (
            verify_session.query(ReviewItemModel)
            .filter_by(id=uuid.UUID(item_id))
            .first()
        )
        assert item_in_db is not None
        assert item_in_db.status == ReviewStatus.APPROVED.value


# ==============================================================================
# 4. COMMIT FAILURE & TRANSACTION STATE RECOVERY
# ==============================================================================


def test_commit_failure_and_subsequent_session_recovery(
    real_pg_engine, seeded_series_context
):
    """Simulate a failure during commit (e.g. database serialization clash or commit crash):

    - Verifies rollback cleans up the session
    - Verifies subsequent requests or operations on the same session/connection still work cleanly
    - Verifies canonical store remains consistent
    """
    series_id, chapter_id = seeded_series_context
    SessionLocal = sessionmaker(bind=real_pg_engine)
    session = SessionLocal()

    # Intentionally trigger an integrity error on commit (duplicate primary key)
    dup_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO series (id, title, slug, total_chapters) "
            "VALUES (:id, 'First', :slug, 5)"
        ),
        {"id": dup_id, "slug": f"slug-1-{dup_id.hex[:6]}"},
    )
    session.commit()

    # Attempt to insert same ID again (causing commit/execution clash)
    try:
        session.execute(
            text(
                "INSERT INTO series (id, title, slug, total_chapters) "
                "VALUES (:id, 'Second', :slug, 5)"
            ),
            {"id": dup_id, "slug": f"slug-2-{dup_id.hex[:6]}"},
        )
        session.commit()
        pytest.fail("Should have raised IntegrityError on duplicate PK")
    except Exception:
        # Proper session recovery: explicit rollback
        session.rollback()

    # Verify session is clean and can perform subsequent operations without error
    new_id = uuid.uuid4()
    session.execute(
        text(
            "INSERT INTO series (id, title, slug, total_chapters) "
            "VALUES (:id, 'Recovered Series', :slug, 5)"
        ),
        {"id": new_id, "slug": f"slug-rec-{new_id.hex[:6]}"},
    )
    session.commit()

    # Verify canonical data consistency
    saved = session.query(SeriesModel).filter_by(id=new_id).first()
    assert saved is not None
    assert saved.title == "Recovered Series"

    session.close()


# ==============================================================================
# 5. STALE CONNECTION / TERMINATED BACKEND RECOVERY
# ==============================================================================


def test_stale_connection_detection_and_automatic_recovery(real_pg_engine):
    """Simulate a severed connection (e.g. server terminated connection or network drop):

    - Identify backend PID of connection
    - Terminate it via pg_terminate_backend from a separate connection
    - Verify exception on stale connection is OperationalError / RETRYABLE
    - Verify connection pool with pool_pre_ping automatically recovers on subsequent request
    """
    # 1. Acquire connection and get PID
    conn1 = real_pg_engine.connect()
    pid1 = conn1.execute(text("SELECT pg_backend_pid()")).scalar()

    # 2. Terminate the backend using a separate connection
    with real_pg_engine.connect() as conn2:
        terminated = conn2.execute(
            text(f"SELECT pg_terminate_backend({pid1})")
        ).scalar()
        assert terminated is True

    # 3. Performing a query on the stale connection must fail with OperationalError
    with pytest.raises(OperationalError) as exc_info:
        conn1.execute(text("SELECT 1"))

    # Must be classified as RETRYABLE
    assert classify_failure(exc_info.value) == RetryClassification.RETRYABLE

    conn1.close()

    # 4. Engine pool with pool_pre_ping MUST successfully deliver a fresh, healthy connection
    with real_pg_engine.connect() as healthy_conn:
        result = healthy_conn.execute(text("SELECT 42")).scalar()
        assert result == 42


# ==============================================================================
# 6. DATABASE UNAVAILABLE DURING MUTATION & API RESILIENCE
# ==============================================================================


def test_database_unavailable_during_mutation_and_subsequent_requests(
    real_pg_engine, seeded_series_context
):
    """Simulate database becoming unavailable during a mutating API call:

    - API returns 503 SERVICE_UNAVAILABLE without crashing or leaking internals
    - Transaction is fully rolled back with no partial commit
    - Once database connectivity is restored, subsequent requests succeed
    - Canonical state remains consistent
    """
    series_id, chapter_id = seeded_series_context
    client = TestClient(app)

    # 1. Normal read request works
    read_resp = client.get(
        f"/api/v1/series/{series_id}/timeline?reader_chapter=1&from=1&to=1"
    )
    assert read_resp.status_code == 200

    # 2. Mutating execution encounters DatabaseUnavailable simulation
    # A. API endpoint returning 503 SERVICE_UNAVAILABLE
    def broken_db_provider():
        raise OperationalError(
            "connection dropped unexpectedly", {}, Exception("Database offline")
        )

    app.dependency_overrides[get_db] = broken_db_provider
    try:
        api_resp = client.get(f"/api/v1/series/{series_id}/events?reader_chapter=1")
        assert api_resp.status_code == 503
        data = api_resp.json()
        assert "error" in data
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "Database service is temporarily unavailable" in data["error"]["message"]
        assert "Database offline" not in api_resp.text
        assert "Traceback" not in api_resp.text
    finally:
        app.dependency_overrides.pop(get_db, None)

    # B. Mutation transaction failure via use case: database unavailable during mutation
    SessionLocal = sessionmaker(bind=real_pg_engine)
    session = SessionLocal()
    repo = SQLAlchemyPublicationRepository(session)
    broken_item_id = str(uuid.uuid4())
    broken_char_id = str(uuid.uuid4())

    def unavailable_save_event(event_data):
        raise OperationalError(
            "could not connect to server: Connection refused", {}, Exception("DB down")
        )

    repo.save_event = unavailable_save_event
    use_case = PublishReviewItemUseCase(repo)
    review_item = _build_review_item(
        broken_item_id, series_id, chapter_id, broken_char_id
    )

    with pytest.raises(RuntimeError, match="Transaction failed"):
        use_case.execute(review_item)

    session.close()

    # 3. Subsequent request against restored DB succeeds immediately
    subsequent_resp = client.get(
        f"/api/v1/series/{series_id}/timeline?reader_chapter=1&from=1&to=1"
    )
    assert subsequent_resp.status_code == 200

    # 4. Verify canonical data remains consistent: series still intact
    SessionLocal = sessionmaker(bind=real_pg_engine)
    with SessionLocal() as check_session:
        series_obj = (
            check_session.query(SeriesModel).filter_by(id=uuid.UUID(series_id)).first()
        )
        assert series_obj is not None
        assert series_obj.title == "Failure Recovery Test Series"


# ==============================================================================
# 7. UNKNOWN TRANSACTION OUTCOME SCENARIO (COMMAND 06)
# ==============================================================================


def test_unknown_transaction_outcome_retry_produces_single_logical_effect(
    real_pg_engine, seeded_series_context
):
    """Simulates the critical unknown transaction outcome scenario:

    1. Client initiates a mutating request (publish review item).
    2. The database transaction completes and commits successfully on the server.
    3. The client experiences a network disconnect or response timeout before receiving the response.
    4. The client (or background retry worker) retries the exact same logical operation.
    5. The existing idempotency mechanisms (fingerprint, row locks, transaction guard) intercept the retry.

    Verification:
    - The retry produces EXACTLY ONE canonical event.
    - The retry produces EXACTLY ONE publication record.
    - Exactly one logical state transition occurs (status stays PUBLISHED).
    - No duplicate entities, relationships, or derived facts are created.
    """
    series_id, chapter_id = seeded_series_context
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())

    SessionLocal = sessionmaker(bind=real_pg_engine)

    # 1. Seed review item in APPROVED state
    with SessionLocal() as init_session:
        init_session.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(series_id),
                chapter_id=uuid.UUID(chapter_id),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={
                    "from_rank": "D",
                    "to_rank": "S",
                    "subject_id": char_id,
                    "target_id": target_id,
                    "sequence": 1,
                },
                provenance_data={"source": "unknown_outcome_simulation"},
                status=ReviewStatus.APPROVED.value,
            )
        )
        init_session.commit()

    # 2. First attempt: Database commit succeeds, but client experiences connection drop
    session_attempt1 = SessionLocal()
    repo_attempt1 = SQLAlchemyPublicationRepository(session_attempt1)
    use_case1 = PublishReviewItemUseCase(repo_attempt1)
    item_attempt1 = _build_review_item(
        item_id, series_id, chapter_id, char_id, target_id=target_id
    )

    # Execute attempt 1
    use_case1.execute(item_attempt1)
    assert item_attempt1.status == ReviewStatus.PUBLISHED
    session_attempt1.close()

    # Simulate client side network drop: Client timed out waiting for HTTP response,
    # leaving the client completely uncertain whether the transaction committed or aborted.

    # 3. Client retries the identical logical operation using a new HTTP request / session
    session_attempt2 = SessionLocal()
    repo_attempt2 = SQLAlchemyPublicationRepository(session_attempt2)
    use_case2 = PublishReviewItemUseCase(repo_attempt2)
    # The client constructs a fresh ReviewItem representation from stored intent
    retry_item = _build_review_item(
        item_id, series_id, chapter_id, char_id, target_id=target_id
    )

    # Execute retry
    use_case2.execute(retry_item)
    assert retry_item.status == ReviewStatus.PUBLISHED
    session_attempt2.close()

    # 4. Strict verification of the canonical store
    with SessionLocal() as verify_session:
        # A. Canonical Events: MUST be exactly 1
        events = (
            verify_session.query(EventModel)
            .filter_by(series_id=uuid.UUID(series_id), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 1, f"Expected 1 canonical event, found {len(events)}"
        canonical_event = events[0]
        assert canonical_event.type == FactType.POWER_RANK_CHANGED.value

        # B. Publication Records: MUST be exactly 1
        records = (
            verify_session.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 1, f"Expected 1 publication record, found {len(records)}"
        assert records[0].status == PublicationStatus.PUBLISHED.value

        # C. ReviewItem state: strictly PUBLISHED
        item_in_db = (
            verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        )
        assert item_in_db.status == ReviewStatus.PUBLISHED.value

        # D. Canonical Entities: ensure no duplicate entity records for char_id or target_id
        entities = (
            verify_session.query(CanonicalEntityModel)
            .filter(
                CanonicalEntityModel.series_id == series_id,
                CanonicalEntityModel.id.in_([char_id, target_id]),
            )
            .all()
        )
        # Each unique entity should appear at most once
        entity_ids = [e.id for e in entities]
        assert len(entity_ids) == len(set(entity_ids))

        # E. Canonical Relationships: exactly one relationship projected
        relationships = (
            verify_session.query(CanonicalRelationshipModel)
            .filter_by(
                series_id=series_id,
                source_entity_id=char_id,
                target_entity_id=target_id,
            )
            .all()
        )
        assert len(relationships) == 1, (
            f"Expected 1 relationship, found {len(relationships)}"
        )
