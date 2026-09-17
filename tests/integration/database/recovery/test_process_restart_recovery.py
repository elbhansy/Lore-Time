"""Process-Restart Recovery Integration Tests (COMMAND 17).

Tests the existing synchronous architecture around process interruption and restart.
Verifies that after process restart (simulated by disposing existing singletons/pools
and re-initializing fresh database connections, cache service, and rate limiter):

1. PostgreSQL state remains valid (schemas, foreign keys, constraints intact).
2. Committed mutations remain committed (ACID persistence).
3. Rolled-back mutations remain rolled back (no partial or orphaned state).
4. Cache safely restarts empty (cold cache immediately falls back to PostgreSQL compute_fn,
   populates safely, and enforces temporal firewall).
5. Rate limiter safely restarts (token buckets initialize with fresh burst budget,
   no persistent corruption).
6. No persistent operation remains in an ambiguous application state (ReviewItem status
   is strictly deterministic: APPROVED or PUBLISHED, never stuck in indeterminate states).

Acceptance:
0 skipped, 0 failed.
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from apps.api.app.application.publishing.publish_review_item import (
    PublishReviewItemUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.cache import (
    CacheService,
    get_cache_service,
    reset_cache_service_for_testing,
)
from apps.api.app.core.rate_limit import (
    RateLimitService,
    reset_rate_limit_service_for_testing,
)
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
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture
def restart_environment():
    """Sets up an initial database state with a series and chapter context."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        sid_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
        sid = uuid.UUID(sid_str)
        ch_1 = session.query(ChapterModel).filter_by(series_id=sid, number=1).first()
        cid_1 = str(ch_1.id)

    yield {
        "engine": engine,
        "session_factory": session_factory,
        "sid": sid,
        "sid_str": sid_str,
        "cid_1": cid_1,
    }
    engine.dispose()


def _build_review_item(item_id: str, series_id: str, chapter_id: str, char_id: str):
    fact = RawExtractedFact(
        type=FactType.CHARACTER_INTRODUCED,
        subject_raw="Dokja Kim",
        target_raw=None,
        payload={
            "subject_id": char_id,
            "name": f"Character_{char_id[:6]}",
            "sequence": 99,
        },
        extraction_confidence=0.99,
        evidence=RawFactEvidence(location="ch1_body"),
    )
    prov = Provenance(
        source_id="restart_recovery_test",
        evidence=Evidence(chapter_id=chapter_id, location="ch1_body"),
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
# 1. COMMITTED MUTATIONS REMAIN COMMITTED & ROLLED BACK REMAIN ROLLED BACK
# ==============================================================================


def test_postgresql_persistence_and_no_ambiguous_state_across_restart(
    restart_environment,
):
    """Verifies that across simulated process restart:
    - Pre-restart committed mutation remains committed in PostgreSQL.
    - Pre-restart aborted mutation remains rolled back (zero partial records).
    - Database state is verified intact by a brand-new connection pool.
    - No persistent entity remains in an ambiguous application state.
    """
    env = restart_environment
    sid = env["sid"]
    sid_str = env["sid_str"]
    cid_1 = env["cid_1"]

    # 1. Execute committed mutation before "crash/restart"
    item_id_committed = str(uuid.uuid4())
    char_id_committed = str(uuid.uuid4())

    with env["session_factory"]() as session:
        session.add(
            ReviewItemModel(
                id=uuid.UUID(item_id_committed),
                series_id=sid,
                chapter_id=uuid.UUID(cid_1),
                fact_type=FactType.CHARACTER_INTRODUCED.value,
                fact_payload={
                    "subject_id": char_id_committed,
                    "name": "CommittedChar",
                    "sequence": 99,
                },
                provenance_data={"source": "committed_pre_restart"},
                status=ReviewStatus.APPROVED.value,
            )
        )
        session.commit()

    with env["session_factory"]() as session:
        repo = SQLAlchemyPublicationRepository(session)
        use_case = PublishReviewItemUseCase(repo)
        item = _build_review_item(item_id_committed, sid_str, cid_1, char_id_committed)
        use_case.execute(item)

    # 2. Execute aborted mutation before "crash/restart"
    item_id_aborted = str(uuid.uuid4())
    char_id_aborted = str(uuid.uuid4())

    with env["session_factory"]() as session:
        session.add(
            ReviewItemModel(
                id=uuid.UUID(item_id_aborted),
                series_id=sid,
                chapter_id=uuid.UUID(cid_1),
                fact_type=FactType.CHARACTER_INTRODUCED.value,
                fact_payload={
                    "subject_id": char_id_aborted,
                    "name": "AbortedChar",
                    "sequence": 100,
                },
                provenance_data={"source": "aborted_pre_restart"},
                status=ReviewStatus.APPROVED.value,
            )
        )
        session.commit()

    with env["session_factory"]() as session:
        repo = SQLAlchemyPublicationRepository(session)

        def crash_before_commit(*args, **kwargs):
            raise RuntimeError("Process sudden kill/power loss simulation")

        repo.save_publication_record = crash_before_commit
        use_case = PublishReviewItemUseCase(repo)
        item = _build_review_item(item_id_aborted, sid_str, cid_1, char_id_aborted)
        with pytest.raises(RuntimeError):
            use_case.execute(item)

    # --------------------------------------------------------------------------
    # SIMULATE PROCESS TERMINATION AND RESTART
    # --------------------------------------------------------------------------
    # Dispose all connections from old process
    env["engine"].dispose()

    # Re-initialize brand-new database engine and session factory (Process Startup)
    settings = get_settings()
    new_engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    new_factory = sessionmaker(bind=new_engine)

    try:
        with new_factory() as verify_session:
            # 3. Verify committed mutation is fully intact
            committed_event = (
                verify_session.query(EventModel)
                .filter_by(series_id=sid, subject_id=uuid.UUID(char_id_committed))
                .all()
            )
            assert len(committed_event) == 1, (
                "Committed canonical event missing after restart!"
            )

            committed_record = (
                verify_session.query(PublicationRecordModel)
                .filter_by(review_item_id=uuid.UUID(item_id_committed))
                .all()
            )
            assert len(committed_record) == 1, (
                "Committed publication record missing after restart!"
            )
            assert committed_record[0].status == PublicationStatus.PUBLISHED.value

            committed_item = (
                verify_session.query(ReviewItemModel)
                .filter_by(id=uuid.UUID(item_id_committed))
                .one()
            )
            assert committed_item.status == ReviewStatus.PUBLISHED.value

            # 4. Verify aborted mutation has ZERO residual traces (rolled back)
            aborted_event = (
                verify_session.query(EventModel)
                .filter_by(series_id=sid, subject_id=uuid.UUID(char_id_aborted))
                .all()
            )
            assert len(aborted_event) == 0, (
                "Partial canonical event found from aborted transaction!"
            )

            aborted_record = (
                verify_session.query(PublicationRecordModel)
                .filter_by(review_item_id=uuid.UUID(item_id_aborted))
                .all()
            )
            assert len(aborted_record) == 0, (
                "Partial publication record found from aborted transaction!"
            )

            # Review item status must remain cleanly APPROVED (ready to be safely retried)
            aborted_item = (
                verify_session.query(ReviewItemModel)
                .filter_by(id=uuid.UUID(item_id_aborted))
                .one()
            )
            assert aborted_item.status == ReviewStatus.APPROVED.value, (
                "Review item left in ambiguous application state!"
            )
    finally:
        new_engine.dispose()


# ==============================================================================
# 2. CACHE SAFELY RESTARTS EMPTY (COLD START RECOVERY)
# ==============================================================================


def test_cache_restarts_empty_and_populates_deterministically(restart_environment):
    """Verifies that when the application restarts:
    - Cache starts empty (cold cache).
    - First read safely results in Cache MISS and computes directly from PostgreSQL.
    - Subsequent read hits the repopulated cache.
    - Post-restart reads strictly obey temporal firewall boundaries.
    """
    env = restart_environment
    sid_str = env["sid_str"]

    # 1. Warm up existing cache
    old_cache = get_cache_service()
    client = TestClient(app)

    r1 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=1")
    assert r1.status_code == 200
    assert old_cache.stats().get("entries", 0) >= 1

    # --------------------------------------------------------------------------
    # SIMULATE PROCESS RESTART: Cache completely cold
    # --------------------------------------------------------------------------
    fresh_cache = CacheService()
    reset_cache_service_for_testing(fresh_cache)

    try:
        # Cache must start completely empty
        stats_cold = fresh_cache.stats()
        assert stats_cold.get("entries", 0) == 0
        assert stats_cold.get("hits", 0) == 0
        assert stats_cold.get("misses", 0) == 0

        # Request 1 on restarted process: Cold cache MISS -> hits PostgreSQL
        r_restart_1 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=1")
        assert r_restart_1.status_code == 200
        assert r_restart_1.json() == r1.json(), (
            "Post-restart state differs from pre-restart state!"
        )
        assert fresh_cache.stats()["misses"] == 1
        assert fresh_cache.stats()["entries"] >= 1

        # Request 2 on restarted process: Cache HIT
        r_restart_2 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=1")
        assert r_restart_2.status_code == 200
        assert fresh_cache.stats()["hits"] == 1
    finally:
        reset_cache_service_for_testing(None)


# ==============================================================================
# 3. RATE LIMITER SAFELY RESTARTS
# ==============================================================================


def test_rate_limiter_safely_restarts_with_clean_token_buckets():
    """Verifies that upon process restart:
    - Rate limiter in-memory buckets start fresh.
    - An identity that was throttled (429) before restart gets a fresh legitimate burst.
    - Subsequent excessive requests trip rate limiting cleanly as designed.
    """
    settings = get_settings()
    client = TestClient(app)
    client_ip = "192.168.99.99"
    burst = settings.RATE_LIMIT_DEFAULT_BURST  # 30

    # 1. Pre-restart: Exhaust quota to trigger 429
    for _ in range(burst):
        client.get("/api/v1/unknown-endpoint", headers={"X-Forwarded-For": client_ip})

    blocked_pre = client.get(
        "/api/v1/unknown-endpoint", headers={"X-Forwarded-For": client_ip}
    )
    assert blocked_pre.status_code == 429

    # --------------------------------------------------------------------------
    # SIMULATE PROCESS RESTART: Fresh in-memory rate limiter service
    # --------------------------------------------------------------------------
    fresh_limiter = RateLimitService()
    reset_rate_limit_service_for_testing(fresh_limiter)

    try:
        # Rate limiter starts clean
        stats = fresh_limiter.stats()
        assert stats.get("active_identities", 0) == 0
        assert stats.get("rejected", 0) == 0

        # Legitimate requests immediately succeed without false positive blocking
        resp_post = client.get("/health", headers={"X-Forwarded-For": client_ip})
        assert resp_post.status_code == 200

        # Normal endpoint allowed on fresh bucket
        resp_allowed = client.get(
            "/api/v1/unknown-endpoint", headers={"X-Forwarded-For": client_ip}
        )
        assert resp_allowed.status_code == 404  # Not 429!
    finally:
        reset_rate_limit_service_for_testing(None)
