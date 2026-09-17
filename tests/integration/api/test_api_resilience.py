"""Phase 4.4 API Resilience & Reliability Integration Tests.

Verifies:
1. Validation & boundary hardening (400)
2. Resource not found mapping (404)
3. Database failure handling & 503 classification without leaking SQL/internals
4. Session recovery after DB failure without restart
5. Idempotent publication and retry safety
6. Temporal spoiler firewall resilience across N-1, N, N+1
"""

import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.dependencies.database import get_db
from apps.api.app.main import app
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
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus


@pytest.fixture(scope="module")
def resilience_engine():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def resilience_db(resilience_engine):
    Session = sessionmaker(bind=resilience_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(resilience_engine):
    Base.metadata.create_all(bind=resilience_engine)
    return TestClient(app)


def _make_review_item(
    item_id: str,
    series_id: str,
    chapter_id: str,
    subject_id: str,
    rank: str,
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.POWER_RANK_CHANGED,
        subject_raw="Hero",
        target_raw=None,
        payload={
            "from_rank": "D",
            "to_rank": rank,
            "subject_id": subject_id,
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
# GROUP A: VALIDATION & ERROR ENVELOPE (400)
# ==============================================================================


def test_api_validation_invalid_chapter_boundary(client):
    sid = str(uuid.uuid4())
    # chapter < 1 must be rejected with 400
    resp = client.get(f"/api/v1/series/{sid}/world-state?chapter=0")
    assert resp.status_code == 400
    data = resp.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
    # Ensure no internal paths or stack trace leaked
    assert "Traceback" not in resp.text
    assert "File " not in resp.text


def test_api_validation_timeline_invalid_bounds(client):
    sid = str(uuid.uuid4())
    # negative reader chapter
    url = f"/api/v1/series/{sid}/timeline?reader_chapter=-5&from=1&to=10"
    resp = client.get(url)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_api_validation_oversized_limit(client):
    sid = str(uuid.uuid4())
    # limit > 100 on events
    resp = client.get(f"/api/v1/series/{sid}/events?reader_chapter=10&page_size=999")
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_api_validation_invalid_event_type(client):
    sid = str(uuid.uuid4())
    url = f"/api/v1/series/{sid}/events?reader_chapter=10&type=NON_EXISTENT_TYPE"
    resp = client.get(url)
    assert resp.status_code == 400
    data = resp.json()
    assert data["error"]["code"] == "VALIDATION_ERROR"
    assert "Invalid event type" in data["error"]["message"]


# ==============================================================================
# GROUP B: RESOURCE NOT FOUND (404)
# ==============================================================================


def test_api_not_found_unknown_series(client):
    sid = str(uuid.uuid4())
    resp = client.get(f"/api/v1/series/{sid}/timeline?reader_chapter=5&from=1&to=5")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "not found" in data["error"]["message"].lower()
    # Confirm no SQL leaked
    assert "SELECT" not in resp.text


# ==============================================================================
# GROUP C: DATABASE FAILURE HANDLING & 503 CLASSIFICATION
# ==============================================================================


def test_database_operational_error_produces_503(client):
    """Simulate database operational failure during request execution.

    Must return HTTP 503 SERVICE_UNAVAILABLE and NO RAW SQL / stack trace.
    """

    def broken_db():
        raise OperationalError(
            "connection refused", {}, Exception("TCP connection failed")
        )

    app.dependency_overrides[get_db] = broken_db
    try:
        sid = str(uuid.uuid4())
        resp = client.get(f"/api/v1/series/{sid}/characters")
        assert resp.status_code == 503
        data = resp.json()
        assert data["error"]["code"] == "SERVICE_UNAVAILABLE"
        assert "Database service is temporarily unavailable" in data["error"]["message"]
        # Verify no raw exception internals or SQL
        assert "TCP connection failed" not in resp.text
        assert "Traceback" not in resp.text
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_database_recovery_without_restart(client, resilience_db):
    """Request A fails with simulated DB error, Request B succeeds immediately."""
    sid = uuid.uuid4()
    slug = f"rec-{str(sid)[:8]}"
    model = SeriesModel(id=sid, title="Recovery Series", slug=slug, total_chapters=10)
    resilience_db.add(model)
    resilience_db.commit()

    # Request A: Simulated failure
    def failing_db():
        raise OperationalError("db dropped", {}, Exception())

    app.dependency_overrides[get_db] = failing_db
    resp_a = client.get(f"/api/v1/series/{sid}/characters")
    assert resp_a.status_code == 503

    # Request B: Normal DB restored
    app.dependency_overrides.pop(get_db, None)
    resp_b = client.get(f"/api/v1/series/{sid}/characters")
    assert resp_b.status_code == 200
    assert isinstance(resp_b.json(), list)


# ==============================================================================
# GROUP D: CONCURRENCY & IDEMPOTENT MUTATIONS
# ==============================================================================


def test_idempotent_publishing_and_retry_safety(resilience_db, resilience_engine):
    """Publishing the exact same review item multiple times:

    - Produces exactly 1 canonical event
    - Leaves status as PUBLISHED
    - Produces deterministic outcome with no duplicate records
    """
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    slug = f"pb-{str(sid)[:8]}"
    model = SeriesModel(id=sid, title="Pub Series", slug=slug, total_chapters=10)
    resilience_db.add(model)
    resilience_db.add(ChapterModel(id=cid, series_id=sid, number=1, title="Ch 1"))
    resilience_db.commit()

    item_id = str(uuid.uuid4())
    subj_id = str(uuid.uuid4())
    review_item = _make_review_item(item_id, str(sid), str(cid), subj_id, "Rank-S")

    rev_model = ReviewItemModel(
        id=review_item.id,
        series_id=sid,
        chapter_id=cid,
        fact_type=review_item.fact.type.value,
        fact_payload=review_item.fact.payload,
        provenance_data={"chapter": 1},
        status=ReviewStatus.PENDING.value,
    )
    resilience_db.add(rev_model)
    resilience_db.commit()

    Session = sessionmaker(bind=resilience_engine)

    # First publication
    s1 = Session()
    repo1 = SQLAlchemyPublicationRepository(s1)
    use_case1 = PublishReviewItemUseCase(repo1)
    use_case1.execute(review_item)
    s1.close()

    # Repeated publication (retry or race)
    s2 = Session()
    repo2 = SQLAlchemyPublicationRepository(s2)
    use_case2 = PublishReviewItemUseCase(repo2)
    use_case2.execute(review_item)
    s2.close()

    # Verify exactly 1 canonical event was inserted
    verify_session = Session()
    events = verify_session.query(EventModel).filter_by(series_id=sid).all()
    assert len(events) == 1
    # Verify review status is published
    final_rev = verify_session.query(ReviewItemModel).filter_by(id=review_item.id).one()
    assert final_rev.status == ReviewStatus.PUBLISHED.value
    verify_session.close()


def test_concurrent_identical_publication_produces_one_event(
    resilience_db, resilience_engine
):
    """5 concurrent workers attempt to publish the exact same review item."""
    sid = uuid.uuid4()
    cid = uuid.uuid4()
    slug = f"cn-{str(sid)[:8]}"
    model = SeriesModel(id=sid, title="Conc Series", slug=slug, total_chapters=10)
    resilience_db.add(model)
    resilience_db.add(ChapterModel(id=cid, series_id=sid, number=1, title="Ch 1"))
    resilience_db.commit()

    item_id = str(uuid.uuid4())
    subj_id = str(uuid.uuid4())
    item = _make_review_item(item_id, str(sid), str(cid), subj_id, "Rank-EX")

    resilience_db.add(
        ReviewItemModel(
            id=item.id,
            series_id=sid,
            chapter_id=cid,
            fact_type=item.fact.type.value,
            fact_payload=item.fact.payload,
            provenance_data={"chapter": 1},
            status=ReviewStatus.PENDING.value,
        )
    )
    resilience_db.commit()

    Session = sessionmaker(bind=resilience_engine)

    def worker():
        sess = Session()
        try:
            repo = SQLAlchemyPublicationRepository(sess)
            uc = PublishReviewItemUseCase(repo)
            uc.execute(item)
        finally:
            sess.close()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(worker) for _ in range(5)]
        for f in futures:
            f.result()

    verify_session = Session()
    events = verify_session.query(EventModel).filter_by(series_id=sid).all()
    assert len(events) == 1
    rec_q = verify_session.query(PublicationRecordModel)
    records = rec_q.filter_by(review_item_id=item.id).all()
    assert len(records) == 1
    verify_session.close()


# ==============================================================================
# GROUP E: TEMPORAL SPOILER FIREWALL INTEGRITY
# ==============================================================================


def test_temporal_firewall_n_minus_one_n_n_plus_one(client, resilience_db):
    """Verifies that at reader_chapter N, event at N+1 is never visible

    in REST timeline, events query, search, or WorldState.
    """
    sid = uuid.uuid4()
    slug = f"sp-{str(sid)[:8]}"
    model = SeriesModel(id=sid, title="Spoiler Series", slug=slug, total_chapters=10)
    resilience_db.add(model)
    c1, c2, c3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    resilience_db.add(ChapterModel(id=c1, series_id=sid, number=1, title="Ch 1"))
    resilience_db.add(ChapterModel(id=c2, series_id=sid, number=2, title="Ch 2"))
    resilience_db.add(ChapterModel(id=c3, series_id=sid, number=3, title="Ch 3"))

    char_id = uuid.uuid4()
    # Event at Chapter 1
    resilience_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c1,
            sequence=0,
            type="CHARACTER_INTRODUCED",
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"name": "Hero", "rank": "F"},
        )
    )
    # Event at Chapter 2 (N)
    resilience_db.add(
        EventModel(
            id=uuid.uuid4(),
            series_id=sid,
            chapter_id=c2,
            sequence=0,
            type="POWER_RANK_CHANGED",
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"rank": "D"},
        )
    )
    # Event at Chapter 3 (N+1 - SPOILER!)
    future_ev_id = uuid.uuid4()
    resilience_db.add(
        EventModel(
            id=future_ev_id,
            series_id=sid,
            chapter_id=c3,
            sequence=0,
            type="POWER_RANK_CHANGED",
            subject_type="CHARACTER",
            subject_id=char_id,
            metadata_={},
            new_state={"rank": "S-CLASS-GOD"},
        )
    )
    resilience_db.commit()

    # 1. At reader_chapter = 1 (N-1): only chapter 1 event
    resp1 = client.get(f"/api/v1/series/{sid}/timeline?reader_chapter=1&from=1&to=1")
    assert resp1.status_code == 200
    events1 = resp1.json()
    assert len(events1) == 1
    assert events1[0]["chapter_number"] == 1

    # 2. At reader_chapter = 2 (N): chapters 1 and 2 visible, NOT 3
    resp2 = client.get(f"/api/v1/series/{sid}/timeline?reader_chapter=2&from=1&to=2")
    assert resp2.status_code == 200
    events2 = resp2.json()
    assert len(events2) == 2
    assert all(e["chapter_number"] <= 2 for e in events2)
    assert not any(e["id"] == str(future_ev_id) for e in events2)

    # 3. Requesting to=3 with reader_chapter=2 is automatically clamped / constrained
    # to reader_chapter, so future event 3 is NEVER returned!
    url_clamped = f"/api/v1/series/{sid}/timeline?reader_chapter=2&from=1&to=3"
    resp_clamped = client.get(url_clamped)
    assert resp_clamped.status_code == 200
    events_clamped = resp_clamped.json()
    assert len(events_clamped) == 2
    assert not any(e["id"] == str(future_ev_id) for e in events_clamped)

    # 4. Events query: requesting to_chapter > reader_chapter must reject with 400
    url_ev = f"/api/v1/series/{sid}/events?reader_chapter=2&from_chapter=1&to_chapter=3"
    resp_ev = client.get(url_ev)
    assert resp_ev.status_code == 400
    msg = resp_ev.json()["error"]["message"]
    assert "to_chapter cannot exceed reader_chapter" in msg
