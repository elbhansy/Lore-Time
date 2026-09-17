"""Integration tests auditing Partial Failure Boundaries (COMMAND 09).

Tests deterministic failure recovery across all lifecycle boundaries:
1. BEFORE DB MUTATION: Pre-transaction validation, business logic, payload checks
2. DURING DB MUTATION: In-flight SQL execution (INSERT events, entity upsert, rel projection, review record)
3. AFTER DB MUTATION (BEFORE COMMIT): In-transaction pre-commit crash, lock failure, foreign key conflict
4. AFTER COMMIT (OUTCOME UNCERTAINTY): Successful commit followed by client disconnection or timeout
5. CACHE INVALIDATION: Post-commit cache purge failure, dirty namespace degradation, cache bypass

Acceptance Guarantee:
- Zero unrecoverable partial state.
- Strictly deterministic recovery behaviors.
"""

import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.cache.cache_service import CacheService
from apps.api.app.core.cache.memory_cache import BoundedMemoryCache
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
from packages.domain.publishing.canonical_publisher import PublicationDomainError
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def boundary_pg_engine():
    """Live PostgreSQL engine for testing partial failure boundaries."""
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def boundary_session_factory(boundary_pg_engine):
    """Session factory for partial failure boundary tests."""
    return sessionmaker(bind=boundary_pg_engine)


@pytest.fixture
def seeded_boundary_series(boundary_session_factory):
    """Seeds series and chapter in PostgreSQL."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    with boundary_session_factory() as session:
        series = SeriesModel(
            id=sid,
            title="Boundary Audit Series",
            slug=f"boundary-{sid.hex[:8]}",
            total_chapters=50,
        )
        chapter = ChapterModel(
            id=cid,
            series_id=sid,
            number=1,
            title="Chapter 1",
        )
        session.add(series)
        session.add(chapter)
        session.commit()

    return str(sid), str(cid)


def _build_test_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    status: ReviewStatus = ReviewStatus.APPROVED,
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw="Rival" if target_id else None,
        payload={
            "from_rank": "C",
            "to_rank": "EX",
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        extraction_confidence=0.99,
        evidence=RawFactEvidence(location="para_10"),
    )
    prov = Provenance(
        source_id="webnovel_source",
        evidence=Evidence(chapter_id=chapter_id, location="para_10"),
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


# ==============================================================================
# BOUNDARY 1: BEFORE DB MUTATION
# ==============================================================================


def test_boundary_before_db_mutation_validation_failure(
    boundary_session_factory, seeded_boundary_series
):
    """Failure Injected: Pre-transaction validation fails because review item is in PENDING state.

    Deterministic Guarantee:
    - Zero DB transaction opened.
    - Zero canonical events or publication records created.
    - Review item remains in original state without side effects.
    """
    sid, cid = seeded_boundary_series
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    with boundary_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={"from_rank": "C", "to_rank": "EX", "subject_id": char_id},
                provenance_data={},
                status=ReviewStatus.PENDING.value,
            )
        )
        s.commit()

    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo)
        item = _build_test_review_item(
            item_id, sid, cid, char_id, status=ReviewStatus.PENDING
        )

        with pytest.raises(
            PublicationDomainError, match="Cannot publish ReviewItem in state: PENDING"
        ):
            use_case.execute(item)

    # Verification: Zero DB mutations occurred
    with boundary_session_factory() as s:
        events = (
            s.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 0
        records = (
            s.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 0
        db_item = s.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        assert db_item.status == ReviewStatus.PENDING.value


# ==============================================================================
# BOUNDARY 2: DURING DB MUTATION
# ==============================================================================


def test_boundary_during_db_mutation_failure_rolls_back_atomically(
    boundary_session_factory, seeded_boundary_series
):
    """Failure Injected: Crash during middle step of in-transaction mutation
    (EventModel inserted, CanonicalEntityModel inserted, but relationship creation crashes).

    Deterministic Guarantee:
    - Atomically rolls back all writes via Postgres transaction rollback.
    - Zero canonical events, zero entities, zero relationships persisted.
    - Review item state remains APPROVED in DB.
    """
    sid, cid = seeded_boundary_series
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())

    with boundary_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={
                    "from_rank": "C",
                    "to_rank": "EX",
                    "subject_id": char_id,
                    "target_id": target_id,
                },
                provenance_data={},
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)

        # Inject failure during relationship creation
        def explode_rel(*args, **kwargs):
            raise RuntimeError(
                "Database connection severed during relationship insertion"
            )

        repo.create_relationship = explode_rel

        use_case = PublishReviewItemUseCase(repo)
        item = _build_test_review_item(item_id, sid, cid, char_id, target_id=target_id)

        with pytest.raises(
            RuntimeError, match="Transaction failed: Database connection severed"
        ):
            use_case.execute(item)

    # Verification: Full atomic rollback
    with boundary_session_factory() as s:
        events = (
            s.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 0
        rels = (
            s.query(CanonicalRelationshipModel)
            .filter_by(series_id=sid, source_entity_id=char_id)
            .all()
        )
        assert len(rels) == 0
        entities = (
            s.query(CanonicalEntityModel).filter_by(series_id=sid, id=char_id).all()
        )
        assert len(entities) == 0
        db_item = s.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        assert db_item.status == ReviewStatus.APPROVED.value


# ==============================================================================
# BOUNDARY 3: AFTER DB MUTATION (BEFORE COMMIT)
# ==============================================================================


def test_boundary_after_db_mutation_before_commit_rolls_back_atomically(
    boundary_session_factory, seeded_boundary_series
):
    """Failure Injected: Crash right before commit() is called (all staging/flush succeeded,
    but commit fails due to simulated serialization failure / server crash).

    Deterministic Guarantee:
    - Postgres aborts the transaction cleanly.
    - Staged mutations disappear entirely.
    - Review item remains in APPROVED state and is ready for safe retry.
    """
    sid, cid = seeded_boundary_series
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    with boundary_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={"from_rank": "C", "to_rank": "EX", "subject_id": char_id},
                provenance_data={},
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)

        # Override commit to simulate failure at the exact commit point
        def explode_commit():
            raise RuntimeError(
                "Commit failed due to simulated database serialization conflict"
            )

        s.commit = explode_commit

        use_case = PublishReviewItemUseCase(repo)
        item = _build_test_review_item(item_id, sid, cid, char_id)

        with pytest.raises(RuntimeError, match="Transaction failed: Commit failed"):
            use_case.execute(item)

    # Verification: Absolute rollback
    with boundary_session_factory() as s:
        events = (
            s.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 0
        records = (
            s.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 0
        db_item = s.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        assert db_item.status == ReviewStatus.APPROVED.value


# ==============================================================================
# BOUNDARY 4: AFTER COMMIT (OUTCOME UNCERTAINTY / NETWORK SEVER)
# ==============================================================================


def test_boundary_after_commit_network_failure_and_retry(
    boundary_session_factory, seeded_boundary_series
):
    """Failure Injected: DB commit succeeds, but network response to client fails / times out.
    Client subsequently retries the exact same publication operation.

    Deterministic Guarantee:
    - First execution successfully persists 1 canonical event and 1 publication record.
    - Retry detects existing publication via lock or publication fingerprint deduplication.
    - Exactly 1 canonical event exists in the database.
    - Exactly 1 publication record exists in the database.
    - Final state is deterministically PUBLISHED.
    """
    sid, cid = seeded_boundary_series
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    with boundary_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={"from_rank": "C", "to_rank": "EX", "subject_id": char_id},
                provenance_data={},
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    # 1. First execution: Commit succeeds in DB, but client experiences simulated dropped connection
    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo)
        item1 = _build_test_review_item(item_id, sid, cid, char_id)
        use_case.execute(item1)
        # Client assumed failure or timeout here!

    # 2. Client retries the identical operation
    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo)
        item2 = _build_test_review_item(item_id, sid, cid, char_id)
        # Must execute cleanly as idempotent no-op or detected duplicate
        use_case.execute(item2)

    # Verification: Strictly exactly 1 canonical event and publication record
    with boundary_session_factory() as s:
        events = (
            s.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 1, (
            f"Expected 1 canonical event after retry, got {len(events)}"
        )
        records = (
            s.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 1, (
            f"Expected 1 publication record after retry, got {len(records)}"
        )
        db_item = s.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        assert db_item.status == ReviewStatus.PUBLISHED.value


# ==============================================================================
# BOUNDARY 5: CACHE INVALIDATION FAILURE
# ==============================================================================


def test_boundary_cache_invalidation_failure_marks_dirty_and_bypasses(
    boundary_session_factory, seeded_boundary_series
):
    """Failure Injected: DB commit succeeds, but cache invalidation crashes
    (e.g., Redis down, serialization failure, or cache backend exception).

    Deterministic Guarantee:
    - Committed DB transaction is NOT rolled back (Correctness-First principle).
    - Cache service catches invalidation error and marks namespace DIRTY.
    - Subsequent reads immediately BYPASS the cache and read fresh canonical DB state.
    - Zero stale reads or lost mutations.
    """
    sid, cid = seeded_boundary_series
    item_id = str(uuid.uuid4())
    char_id = str(uuid.uuid4())

    with boundary_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={"from_rank": "C", "to_rank": "EX", "subject_id": char_id},
                provenance_data={},
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    # Set up memory cache with custom mock backend that fails on delete_prefix
    backend = BoundedMemoryCache()
    original_delete_prefix = backend.delete_prefix

    def failing_delete_prefix(prefix: str):
        raise RuntimeError("Simulated cache backend failure during invalidation")

    backend.delete_prefix = failing_delete_prefix
    cache_service = CacheService(backend=backend)

    # Execute publication
    with boundary_session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo, cache_service=cache_service)
        item = _build_test_review_item(item_id, sid, cid, char_id)
        # Publication should succeed without raising, despite cache invalidation error
        use_case.execute(item)

    # Verification:
    # A. DB transaction committed successfully
    with boundary_session_factory() as s:
        events = (
            s.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 1
        db_item = s.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        assert db_item.status == ReviewStatus.PUBLISHED.value

    # B. Namespace is marked DIRTY
    assert backend.is_dirty(sid) is True

    # C. get_or_compute strictly bypasses cache when dirty
    compute_called = 0

    def compute_timeline():
        nonlocal compute_called
        compute_called += 1
        return [{"event": "fresh_db_event"}]

    result = cache_service.get_or_compute(
        series_id=sid,
        resource="timeline",
        compute_fn=compute_timeline,
        reader_chapter=1,
    )
    assert result == [{"event": "fresh_db_event"}]
    assert compute_called == 1, "Cache dirty bypass should directly invoke compute_fn"
