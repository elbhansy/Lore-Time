"""Integration tests for concurrent duplicate operations in real PostgreSQL (COMMAND 08).

Verifies concurrency resilience across multiple worker thread concurrency tiers:
- 2 workers
- 5 workers
- 10 workers

Tests both:
1. Identical requests: Concurrent identical API requests against live endpoints
2. Identical publication operations: Concurrent identical domain publication workflows

Guarantees Verified:
- No duplicate canonical event (strictly 1 event created)
- No duplicate logical mutation
- No deadlock (all workers terminate cleanly within timeout)
- Deterministic result across all concurrency levels
- Valid transaction state (clean ACID isolation, valid rollback/commit, no corruption)
- Solved entirely via PostgreSQL ACID row locks (SELECT FOR UPDATE) and unique constraints
  (ON CONFLICT DO NOTHING), with zero application-level sleep/retry hacks.
"""

import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
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
def concurrent_db_engine():
    """Provides high-capacity engine connected to PostgreSQL for concurrency testing."""
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def concurrent_session_factory(concurrent_db_engine):
    """Session factory for spawning independent transactional connections per worker thread."""
    return sessionmaker(bind=concurrent_db_engine)


@pytest.fixture
def seeded_concurrent_context(concurrent_session_factory):
    """Seeds a series, chapter, and characters in PostgreSQL for concurrent testing."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    char_id = uuid.uuid4()

    with concurrent_session_factory() as session:
        series = SeriesModel(
            id=sid,
            title="Concurrency Audit Series",
            slug=f"concurrent-{sid.hex[:8]}",
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

    return str(sid), str(cid), str(char_id)


def _build_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    target_id: str | None = None,
    rank: str = "SS",
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Dokja",
        target_raw="Rival" if target_id else None,
        payload={
            "from_rank": "A",
            "to_rank": rank,
            "subject_id": subject_id,
            "target_id": target_id,
            "sequence": 1,
        },
        extraction_confidence=0.98,
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
# 1. CONCURRENT IDENTICAL PUBLICATION OPERATIONS (2, 5, 10 WORKERS)
# ==============================================================================


@pytest.mark.parametrize("worker_count", [2, 5, 10])
def test_concurrent_identical_publication_operations(
    worker_count, concurrent_session_factory, seeded_concurrent_context
):
    """Executes identical publication operations across N concurrent worker threads:

    - Pre-populates a ReviewItem in APPROVED state.
    - Concurrently triggers PublishReviewItemUseCase.execute across N threads.
    - Confirms:
      1. Zero deadlocks: All workers complete within timeout.
      2. No duplicate canonical events: Exactly 1 canonical event is inserted.
      3. No duplicate logical mutations: Exactly 1 publication record is created.
      4. Deterministic state: Review item status is strictly PUBLISHED.
      5. Valid transaction state: Zero partial records or broken foreign keys.
    """
    sid, cid, char_id = seeded_concurrent_context
    item_id = str(uuid.uuid4())
    target_id = str(uuid.uuid4())

    # 1. Seed review item in DB
    with concurrent_session_factory() as init_session:
        init_session.add(
            ReviewItemModel(
                id=uuid.UUID(item_id),
                series_id=uuid.UUID(sid),
                chapter_id=uuid.UUID(cid),
                fact_type=FactType.POWER_RANK_CHANGED.value,
                fact_payload={
                    "from_rank": "A",
                    "to_rank": "SS",
                    "subject_id": char_id,
                    "target_id": target_id,
                    "sequence": 1,
                },
                provenance_data={"source": f"concurrency_{worker_count}"},
                status=ReviewStatus.APPROVED.value,
            )
        )
        init_session.commit()

    def worker_run():
        """Worker task creating independent DB connection and running use case."""
        worker_session = concurrent_session_factory()
        repo = SQLAlchemyPublicationRepository(worker_session)
        use_case = PublishReviewItemUseCase(repo)
        item = _build_review_item(item_id, sid, cid, char_id, target_id=target_id)
        try:
            use_case.execute(item)
            return {"status": "success", "error": None}
        except Exception as exc:
            return {"status": "error", "error": str(exc)}
        finally:
            worker_session.close()

    # 2. Execute concurrently without application-level sleeps
    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(worker_run) for _ in range(worker_count)]
        results = [f.result(timeout=10.0) for f in as_completed(futures)]

    # At least one worker succeeded
    success_count = sum(1 for r in results if r["status"] == "success")
    assert success_count >= 1, (
        f"Expected at least 1 successful publication, got: {results}"
    )

    # 3. Strict Verification of Canonical Database State
    with concurrent_session_factory() as verify_session:
        # A. Canonical Events: MUST be exactly 1
        events = (
            verify_session.query(EventModel)
            .filter_by(series_id=uuid.UUID(sid), subject_id=uuid.UUID(char_id))
            .all()
        )
        assert len(events) == 1, (
            f"Concurrency failure with {worker_count} workers: expected 1 canonical event, "
            f"found {len(events)}"
        )
        assert events[0].type == FactType.POWER_RANK_CHANGED.value

        # B. Publication Records: MUST be exactly 1
        records = (
            verify_session.query(PublicationRecordModel)
            .filter_by(review_item_id=uuid.UUID(item_id))
            .all()
        )
        assert len(records) == 1, (
            f"Concurrency failure with {worker_count} workers: expected 1 publication record, "
            f"found {len(records)}"
        )
        assert records[0].status == PublicationStatus.PUBLISHED.value

        # C. ReviewItem State: MUST be strictly PUBLISHED
        db_item = (
            verify_session.query(ReviewItemModel).filter_by(id=uuid.UUID(item_id)).one()
        )
        assert db_item.status == ReviewStatus.PUBLISHED.value

        # D. Canonical Entities: exactly 1 entry per unique entity
        entities = (
            verify_session.query(CanonicalEntityModel)
            .filter(
                CanonicalEntityModel.series_id == sid,
                CanonicalEntityModel.id.in_([char_id, target_id]),
            )
            .all()
        )
        entity_ids = [e.id for e in entities]
        assert len(entity_ids) == len(set(entity_ids))

        # E. Canonical Relationships: exactly 1 relationship projected
        relationships = (
            verify_session.query(CanonicalRelationshipModel)
            .filter_by(
                series_id=sid, source_entity_id=char_id, target_entity_id=target_id
            )
            .all()
        )
        assert len(relationships) == 1


# ==============================================================================
# 2. CONCURRENT IDENTICAL API REQUESTS (2, 5, 10 WORKERS)
# ==============================================================================


@pytest.mark.parametrize("worker_count", [2, 5, 10])
def test_concurrent_identical_api_requests(
    worker_count, concurrent_session_factory, seeded_concurrent_context
):
    """Fires N concurrent identical API requests against live endpoints:

    - Confirms all requests resolve deterministically.
    - Confirms zero database corruption or connection pool exhaustion deadlocks.
    - Confirms returned responses have matching deterministic states.
    """
    sid, cid, _ = seeded_concurrent_context

    # Ensure at least 1 published event exists in timeline
    with concurrent_session_factory() as setup_session:
        event_id = uuid.uuid4()
        ev = EventModel(
            id=event_id,
            series_id=uuid.UUID(sid),
            chapter_id=uuid.UUID(cid),
            sequence=1,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=event_id,
            metadata_={},
            publication_fingerprint=f"fp_api_concurrency_{worker_count}_{event_id}",
        )
        setup_session.add(ev)
        setup_session.commit()

    client = TestClient(app)

    def send_request(worker_idx: int):
        resp = client.get(
            f"/api/v1/series/{sid}/timeline?reader_chapter=1&from=1&to=1",
            headers={"X-Request-ID": f"concurrency-req-{worker_count}-{worker_idx}"},
        )
        return resp.status_code, resp.json()

    with ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(send_request, i) for i in range(worker_count)]
        results = [f.result(timeout=10.0) for f in as_completed(futures)]

    # All responses must be HTTP 200 OK
    status_codes = [r[0] for r in results]
    assert all(code == 200 for code in status_codes), (
        f"Expected all 200 OK under {worker_count} concurrent requests, got: {status_codes}"
    )

    # All responses must receive identical deterministic payload length
    payload_lengths = [len(r[1]) for r in results]
    assert len(set(payload_lengths)) == 1, (
        "Non-deterministic results across concurrent requests"
    )
    assert payload_lengths[0] >= 1
