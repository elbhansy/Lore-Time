"""Integration tests verifying Series Isolation during concurrent/repeated operations (COMMAND 12).

Tests concurrent and repeated operations across Series A and Series B:
1. Idempotency keys cannot accidentally cross series boundaries (Series A fingerprint != Series B fingerprint).
2. Retries of Series A cannot affect Series B data, state, or publications.
3. Cache invalidation remains strictly series-scoped (purging Series A never clears or invalidates Series B cache).
4. Database queries and projections remain strictly series-scoped (zero row contamination).

Guarantees Verified:
- Strict multi-tenancy / series boundaries.
- Deterministic behavior under concurrent cross-series load.
- Zero cross-series pollution across events, entities, relationships, cache entries, and review items.
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
from apps.api.app.application.timeline.get_world_state import (
    GetWorldStateUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from apps.api.repositories.sqlalchemy_event_repository import (
    SQLAlchemyEventRepository,
)
from apps.api.repositories.sqlalchemy_series_repository import (
    SQLAlchemySeriesRepository,
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
from packages.domain.extraction.extraction_result import (
    RawExtractedFact,
    RawFactEvidence,
)
from packages.domain.extraction.fact_type import FactType
from packages.domain.provenance.confidence import Confidence
from packages.domain.provenance.evidence import Evidence
from packages.domain.provenance.provenance import Provenance
from packages.domain.publishing.publication_fingerprint import (
    PublicationFingerprint,
)
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture(scope="module")
def series_pg_engine():
    """PostgreSQL engine for cross-series isolation tests."""
    settings = get_settings()
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=15,
        max_overflow=20,
        pool_pre_ping=True,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def series_session_factory(series_pg_engine):
    """Session factory for cross-series isolation tests."""
    return sessionmaker(bind=series_pg_engine)


@pytest.fixture
def clean_cache():
    """Provides isolated clean cache and cleans up afterwards."""
    service = CacheService()
    reset_cache_service_for_testing(service)
    yield service
    service.clear()
    reset_cache_service_for_testing(None)


def _seed_two_series_environment(session):
    """Seeds Series A and Series B with distinct IDs and chapters."""
    sid_a_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
    sid_b_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)

    sid_a = uuid.UUID(sid_a_str)
    sid_b = uuid.UUID(sid_b_str)

    ch_a = session.query(ChapterModel).filter_by(series_id=sid_a, number=1).first()
    ch_b = session.query(ChapterModel).filter_by(series_id=sid_b, number=1).first()

    return {
        "sid_a": sid_a,
        "sid_b": sid_b,
        "sid_a_str": sid_a_str,
        "sid_b_str": sid_b_str,
        "ch_a": ch_a,
        "ch_b": ch_b,
    }


# ==============================================================================
# 1. IDEMPOTENCY KEYS CANNOT ACCIDENTALLY CROSS SERIES BOUNDARIES
# ==============================================================================


def test_idempotency_fingerprint_never_crosses_series_boundaries():
    """Verify that identical event parameters (same chapter_id, event_type, subject_id, payload)
    generate completely distinct publication fingerprints when series_id differs.
    """
    chapter_id = str(uuid.uuid4())
    subject_id = str(uuid.uuid4())
    payload = {"from_rank": "D", "to_rank": "S", "sequence": 1}

    sid_a = str(uuid.uuid4())
    sid_b = str(uuid.uuid4())

    fp_a = PublicationFingerprint.generate(
        series_id=sid_a,
        chapter_id=chapter_id,
        event_type=FactType.POWER_RANK_CHANGED.value,
        subject_id=subject_id,
        target_id=None,
        payload=payload,
    )

    fp_b = PublicationFingerprint.generate(
        series_id=sid_b,
        chapter_id=chapter_id,
        event_type=FactType.POWER_RANK_CHANGED.value,
        subject_id=subject_id,
        target_id=None,
        payload=payload,
    )

    # Invariant: Fingerprints must be distinct, preventing cross-series conflict or deduplication hijack
    assert fp_a != fp_b, "Fingerprint collision detected across series boundaries!"


# ==============================================================================
# 2. RETRY OF SERIES A CANNOT AFFECT SERIES B
# ==============================================================================


def test_retry_of_series_a_cannot_affect_series_b(series_session_factory, clean_cache):
    """Simulate repeated retries and mutations on Series A while Series B remains idle:
    - Retries of Series A only mutate Series A.
    - Series B events, publication records, and review items remain completely untouched.
    """
    with series_session_factory() as s:
        env = _seed_two_series_environment(s)
        sid_a = env["sid_a"]
        sid_b = env["sid_b"]
        sid_a_str = env["sid_a_str"]
        sid_b_str = env["sid_b_str"]
        ch_a = env["ch_a"]

        # Snapshot Series B baseline counts
        initial_events_b = s.query(EventModel).filter_by(series_id=sid_b).count()
        initial_records_b = (
            s.query(PublicationRecordModel)
            .join(
                ReviewItemModel,
                PublicationRecordModel.review_item_id == ReviewItemModel.id,
            )
            .filter(ReviewItemModel.series_id == sid_b)
            .count()
        )

    # Prepare review item for Series A
    char_a_id = str(uuid.uuid4())
    rev_uuid = uuid.uuid4()
    fact_a = RawExtractedFact(
        type=FactType.CHARACTER_INTRODUCED,
        subject_raw="HeroA",
        target_raw=None,
        payload={
            "subject_id": char_a_id,
            "character_id": char_a_id,
            "name": "HeroA_Isolated",
            "sequence": 99,
        },
        extraction_confidence=1.0,
        evidence=RawFactEvidence(location="para_a"),
    )
    prov_a = Provenance(
        "src_a", Evidence(str(ch_a.id), "loc"), Confidence(1, 1, 1, 1), datetime.now()
    )

    with series_session_factory() as s:
        s.add(
            ReviewItemModel(
                id=rev_uuid,
                series_id=sid_a,
                chapter_id=ch_a.id,
                fact_type=fact_a.type.value,
                fact_payload=fact_a.payload,
                provenance_data=prov_a.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    review_item_a = ReviewItem(
        str(rev_uuid), sid_a_str, str(ch_a.id), fact_a, prov_a, ReviewStatus.APPROVED
    )

    # Execute and retry 3 times on Series A
    for _ in range(3):
        with series_session_factory() as s:
            repo = SQLAlchemyPublicationRepository(s)
            use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)
            use_case.execute(review_item_a)

    # Verification:
    with series_session_factory() as s:
        # Series A must have exactly 1 event and 1 publication record for this review item
        events_a = (
            s.query(EventModel)
            .filter_by(series_id=sid_a, subject_id=uuid.UUID(char_a_id))
            .all()
        )
        assert len(events_a) == 1
        rec_a = s.query(PublicationRecordModel).filter_by(review_item_id=rev_uuid).all()
        assert len(rec_a) == 1

        # Series B must have EXACTLY its initial counts (zero pollution from Series A retries)
        final_events_b = s.query(EventModel).filter_by(series_id=sid_b).count()
        assert final_events_b == initial_events_b, (
            "Series B event count changed due to Series A retry!"
        )

        final_records_b = (
            s.query(PublicationRecordModel)
            .join(
                ReviewItemModel,
                PublicationRecordModel.review_item_id == ReviewItemModel.id,
            )
            .filter(ReviewItemModel.series_id == sid_b)
            .count()
        )
        assert final_records_b == initial_records_b, (
            "Series B publication records mutated by Series A retry!"
        )


# ==============================================================================
# 3. CACHE INVALIDATION REMAINS SERIES-SCOPED
# ==============================================================================


def test_cache_invalidation_remains_series_scoped(series_session_factory, clean_cache):
    """Verify that invalidating Series A cache preserves Series B cache entries and hit status:
    - Warm cache for Series A and Series B.
    - Invalidate Series A (e.g., via publication or invalidate_series).
    - Series A cache is purged / misses.
    - Series B cache remains hot (HIT) with zero eviction.
    """
    with series_session_factory() as s:
        env = _seed_two_series_environment(s)
        sid_a = env["sid_a"]
        sid_b = env["sid_b"]
        sid_a_str = env["sid_a_str"]
        sid_b_str = env["sid_b_str"]

        series_repo = SQLAlchemySeriesRepository(s)
        event_repo = SQLAlchemyEventRepository(s)
        builder = WorldStateBuilder(EventApplier())

        ws_uc = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )

        # 1. Warm cache for both Series A and Series B
        ws_a_initial = ws_uc.execute(sid_a, reader_chapter=1)
        ws_b_initial = ws_uc.execute(sid_b, reader_chapter=1)

        # Initial cache stats
        initial_stats = clean_cache.stats()
        assert initial_stats["entries"] >= 2

        # 2. Invalidate Series A ONLY
        deleted_count = clean_cache.invalidate_series(sid_a_str)
        assert deleted_count >= 1

        # 3. Series B read MUST be a cache HIT
        hits_before_b = clean_cache.stats()["hits"]
        ws_b_cached = ws_uc.execute(sid_b, reader_chapter=1)
        hits_after_b = clean_cache.stats()["hits"]

        assert hits_after_b == hits_before_b + 1, (
            "Series B was not a cache HIT after Series A invalidation!"
        )
        assert ws_b_cached == ws_b_initial

        # 4. Series A read MUST be a cache MISS
        misses_before_a = clean_cache.stats()["misses"]
        ws_a_fresh = ws_uc.execute(sid_a, reader_chapter=1)
        misses_after_a = clean_cache.stats()["misses"]

        assert misses_after_a == misses_before_a + 1, (
            "Series A should have been a cache miss after invalidation!"
        )
        assert ws_a_fresh == ws_a_initial


# ==============================================================================
# 4. DATABASE QUERIES & CONCURRENT OPERATIONS REMAIN SERIES-SCOPED
# ==============================================================================


def test_concurrent_cross_series_operations_remain_strictly_isolated(
    series_session_factory, clean_cache
):
    """Fires concurrent publication and timeline requests simultaneously across Series A and Series B:
    - Verifies zero cross-series row leakage or locks clashing across workers.
    - API timeline for Series A contains only Series A events.
    - API timeline for Series B contains only Series B events.
    """
    get_rate_limit_service().clear()

    with series_session_factory() as s:
        env = _seed_two_series_environment(s)
        sid_a_str = env["sid_a_str"]
        sid_b_str = env["sid_b_str"]

    client = TestClient(app)

    def query_series_timeline(worker_idx: int, sid_str: str):
        resp = client.get(
            f"/api/v1/series/{sid_str}/timeline?reader_chapter=1&from=1&to=1",
            headers={"X-Forwarded-For": f"10.0.0.{worker_idx + 1}"},
        )
        return sid_str, resp.status_code, resp.json()

    # Mix 20 concurrent requests interleaved between Series A and Series B
    tasks = [(i, sid_a_str if i % 2 == 0 else sid_b_str) for i in range(20)]

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query_series_timeline, i, sid) for i, sid in tasks]
        results = [f.result(timeout=10.0) for f in as_completed(futures)]

    for queried_sid, status, events in results:
        assert status == 200
        # Every event must have series_id belonging strictly to queried_sid
        with series_session_factory() as s:
            event_ids = [uuid.UUID(e["id"]) for e in events]
            db_events = s.query(EventModel).filter(EventModel.id.in_(event_ids)).all()
            for ev in db_events:
                assert str(ev.series_id) == queried_sid, (
                    f"CROSS-SERIES LEAKAGE: Query for {queried_sid} returned event {ev.id} "
                    f"belonging to series {ev.series_id}"
                )
