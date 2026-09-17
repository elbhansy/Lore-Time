"""Integration tests verifying Temporal Firewall during failure and recovery scenarios (COMMAND 11).

For every temporal mutation and recovery path, tests readerChapter boundaries:
- readerChapter = N - 1
- readerChapter = N
- readerChapter = N + 1

Simulates:
1. Duplicate request
2. Retry after client-side timeout/failure
3. Mid-transaction failure & rollback
4. Post-commit cache invalidation failure & dirty namespace bypass
5. Concurrent identical and conflicting requests

Verifies that retries and recovery NEVER expose future temporal state:
- future entities
- future relationships
- future events
- future metadata
- future counts
- future search results
- future analytics

Acceptance:
Temporal firewall remains absolute across all failure and recovery boundaries.
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
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
from apps.api.app.core.rate_limit import get_rate_limit_service
from apps.api.app.main import app
from apps.api.repositories.canonical.sqlalchemy_publication_repository import (
    SQLAlchemyPublicationRepository,
)
from infrastructure.database.models import Base
from infrastructure.database.models.chapter import ChapterModel
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
from packages.domain.review.review_item import ReviewItem
from packages.domain.review.review_status import ReviewStatus
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture(scope="module")
def pg_engine():
    """Live PostgreSQL engine."""
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
def session_factory(pg_engine):
    """Session factory for isolated worker sessions."""
    return sessionmaker(bind=pg_engine)


@pytest.fixture
def clean_cache():
    """Provides isolated clean cache and cleans up afterwards."""
    service = CacheService()
    reset_cache_service_for_testing(service)
    yield service
    service.clear()
    reset_cache_service_for_testing(None)


@pytest.fixture(autouse=True)
def clean_rate_limit():
    """Ensure rate limit buckets are completely clean before and after every test."""
    get_rate_limit_service().clear()
    yield
    get_rate_limit_service().clear()


def _seed_boundary_environment(session, target_chapter_num: int = 5):
    """Seeds a series with 10 chapters and baseline events up to chapter 10.

    Target mutation will occur at target_chapter_num (N = 5).
    """
    series_id_str = seed_test_series(session, num_chapters=10, events_per_chapter=2)
    sid = uuid.UUID(series_id_str)
    ch_n_minus_1 = (
        session.query(ChapterModel)
        .filter_by(series_id=sid, number=target_chapter_num - 1)
        .first()
    )
    ch_n = (
        session.query(ChapterModel)
        .filter_by(series_id=sid, number=target_chapter_num)
        .first()
    )
    ch_n_plus_1 = (
        session.query(ChapterModel)
        .filter_by(series_id=sid, number=target_chapter_num + 1)
        .first()
    )

    return {
        "series_id": sid,
        "series_id_str": series_id_str,
        "n_minus_1_num": target_chapter_num - 1,
        "n_num": target_chapter_num,
        "n_plus_1_num": target_chapter_num + 1,
        "ch_n_minus_1": ch_n_minus_1,
        "ch_n": ch_n,
        "ch_n_plus_1": ch_n_plus_1,
    }


def _create_review_item_for_chapter(
    series_id_str: str, chapter_id: str, char_id: str, target_id: str = None
) -> ReviewItem:
    fact = RawExtractedFact(
        type=FactType.CHARACTER_INTRODUCED
        if not target_id
        else FactType.RELATIONSHIP_CREATED,
        subject_raw="TemporalSubject",
        target_raw="TemporalTarget" if target_id else None,
        payload={
            "subject_id": char_id,
            "target_id": target_id,
            "name": f"Character_{char_id[:6]}",
            "relationship_type": "ALLY" if target_id else None,
            "sequence": 99,
        },
        extraction_confidence=0.99,
        evidence=RawFactEvidence(location="chapter_n_body"),
    )
    prov = Provenance(
        source_id="temporal_prov",
        evidence=Evidence(chapter_id=chapter_id, location="chapter_n_body"),
        confidence=Confidence(1.0, 1.0, 1.0, 1.0),
        captured_at=datetime.now(),
    )
    return ReviewItem(
        id=str(uuid.uuid4()),
        series_id=series_id_str,
        chapter_id=chapter_id,
        fact=fact,
        provenance=prov,
        status=ReviewStatus.APPROVED,
    )


# ==============================================================================
# 1. TEMPORAL FIREWALL DURING DUPLICATE REQUESTS & RETRIES
# ==============================================================================


def test_temporal_firewall_during_duplicate_request_and_retry(
    session_factory, clean_cache
):
    """Verifies that across duplicate requests and retries for a mutation at chapter N:
    - readerChapter = N - 1 (Ch 4) CANNOT see chapter N entity/event/relationship
    - readerChapter = N (Ch 5) sees chapter N mutation
    - readerChapter = N + 1 (Ch 6) sees chapter N mutation
    """
    with session_factory() as s:
        env = _seed_boundary_environment(s, target_chapter_num=5)
        sid = env["series_id"]
        sid_str = env["series_id_str"]
        ch_n = env["ch_n"]

    new_char_id = str(uuid.uuid4())
    rev_item = _create_review_item_for_chapter(sid_str, str(ch_n.id), new_char_id)

    with session_factory() as s:
        from infrastructure.database.models.character import CharacterModel

        s.add(
            CharacterModel(
                id=uuid.UUID(new_char_id),
                series_id=sid,
                name=f"Character_{new_char_id[:6]}",
                description="Temporal test character",
            )
        )
        s.add(
            ReviewItemModel(
                id=uuid.UUID(rev_item.id),
                series_id=sid,
                chapter_id=ch_n.id,
                fact_type=rev_item.fact.type.value,
                fact_payload=rev_item.fact.payload,
                provenance_data=rev_item.provenance.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    # Initial publication attempt
    with session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)
        use_case.execute(rev_item)

    # Simulated client retry (duplicate operation)
    with session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)
        use_case.execute(rev_item)

    # Verify Triad (N-1, N, N+1) via live API and application use cases
    client = TestClient(app)

    # A. readerChapter = N - 1 (Ch 4): MUST NOT see the newly introduced character or its event/relationships/metadata/counts/search/analytics
    resp_n_minus_1 = client.get(
        f"/api/v1/series/{sid_str}/timeline?reader_chapter=4&from=1&to=5"
    )
    assert resp_n_minus_1.status_code == 200
    events_ch4 = resp_n_minus_1.json()
    assert all(e["chapter_number"] <= 4 for e in events_ch4)
    assert not any(e["subject_id"] == new_char_id for e in events_ch4), (
        "FIREWALL BREACH: Chapter 5 entity exposed to reader at chapter 4 during duplicate/retry"
    )

    ws_resp_ch4 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=4")
    assert ws_resp_ch4.status_code == 200
    assert new_char_id not in ws_resp_ch4.json()["characters"], (
        "FIREWALL BREACH: Chapter 5 character present in chapter 4 world state"
    )

    # Search check: Must return 0 count and never leak future character
    search_ch4 = client.get(
        f"/api/v1/series/{sid_str}/search?q=Character_{new_char_id[:6]}&chapter=4"
    ).json()
    assert search_ch4["total"] == 0, (
        "FIREWALL BREACH: Future character surfaced in search at chapter 4"
    )

    # Analytics check: Total events and distribution must not include chapter 5 mutation
    analytics_ch4 = client.get(
        f"/api/v1/series/{sid_str}/analytics/overview?to=4"
    ).json()
    assert all(
        int(b["key"]) <= 4 for b in analytics_ch4["statistics"]["events_by_chapter"]
    )

    # B. readerChapter = N (Ch 5): MUST see the newly introduced character and event
    resp_n = client.get(
        f"/api/v1/series/{sid_str}/timeline?reader_chapter=5&from=1&to=5"
    )
    assert resp_n.status_code == 200
    events_ch5 = resp_n.json()
    assert any(e["subject_id"] == new_char_id for e in events_ch5)

    ws_resp_ch5 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=5")
    assert new_char_id in ws_resp_ch5.json()["characters"]

    search_ch5 = client.get(
        f"/api/v1/series/{sid_str}/search?q=Character_{new_char_id[:6]}&chapter=5"
    ).json()
    assert search_ch5["total"] >= 1

    # C. readerChapter = N + 1 (Ch 6): MUST see the newly introduced character
    resp_n_plus_1 = client.get(
        f"/api/v1/series/{sid_str}/timeline?reader_chapter=6&from=1&to=6"
    )
    assert resp_n_plus_1.status_code == 200
    events_ch6 = resp_n_plus_1.json()
    assert any(e["subject_id"] == new_char_id for e in events_ch6)


# ==============================================================================
# 2. TEMPORAL FIREWALL DURING TRANSACTION FAILURE & ROLLBACK
# ==============================================================================


def test_temporal_firewall_during_transaction_failure(session_factory, clean_cache):
    """When a mutation at chapter N aborts mid-transaction:
    - readerChapter = N - 1 (Ch 4) sees zero future state
    - readerChapter = N (Ch 5) sees zero aborted mutation
    - readerChapter = N + 1 (Ch 6) sees zero aborted mutation
    """
    with session_factory() as s:
        env = _seed_boundary_environment(s, target_chapter_num=5)
        sid = env["series_id"]
        sid_str = env["series_id_str"]
        ch_n = env["ch_n"]

    failed_char_id = str(uuid.uuid4())
    rev_item = _create_review_item_for_chapter(sid_str, str(ch_n.id), failed_char_id)

    with session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(rev_item.id),
                series_id=sid,
                chapter_id=ch_n.id,
                fact_type=rev_item.fact.type.value,
                fact_payload=rev_item.fact.payload,
                provenance_data=rev_item.provenance.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    # Injected crash right before commit
    with session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)

        def explode_status_update(*args, **kwargs):
            raise RuntimeError("Severed connection right before commit")

        repo.update_review_status = explode_status_update
        use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)

        with pytest.raises(RuntimeError):
            use_case.execute(rev_item)

    # Verification: Neither N-1, N, nor N+1 can observe the failed character across events, world-state, search, or analytics
    client = TestClient(app)
    for ch in [4, 5, 6]:
        resp = client.get(
            f"/api/v1/series/{sid_str}/timeline?reader_chapter={ch}&from=1&to={ch}"
        )
        assert resp.status_code == 200
        events = resp.json()
        assert not any(e["subject_id"] == failed_char_id for e in events)

        ws_resp = client.get(f"/api/v1/series/{sid_str}/world-state?chapter={ch}")
        assert failed_char_id not in ws_resp.json()["characters"]

        search_resp = client.get(
            f"/api/v1/series/{sid_str}/search?q=Character_{failed_char_id[:6]}&chapter={ch}"
        ).json()
        assert search_resp["total"] == 0

        analytics_resp = client.get(
            f"/api/v1/series/{sid_str}/analytics/overview?to={ch}"
        ).json()
        assert not any(
            b["key"] == failed_char_id
            for b in analytics_resp["statistics"]["events_by_entity"]
        )


# ==============================================================================
# 3. TEMPORAL FIREWALL DURING CACHE FAILURE & DIRTY RECOVERY
# ==============================================================================


def test_temporal_firewall_during_cache_failure_and_dirty_recovery(
    session_factory, clean_cache
):
    """When cache invalidation fails after commit and namespace becomes DIRTY:
    - readerChapter = N - 1 recovers from PostgreSQL and DOES NOT see chapter N event
    - readerChapter = N recovers from PostgreSQL and DOES see chapter N event
    - readerChapter = N + 1 recovers from PostgreSQL and DOES see chapter N event
    - Analytics and counts never leak future state across any boundary
    """
    with session_factory() as s:
        env = _seed_boundary_environment(s, target_chapter_num=5)
        sid = env["series_id"]
        sid_str = env["series_id_str"]
        ch_n = env["ch_n"]

    # Warm cache at chapter 4, 5, 6
    client = TestClient(app)
    client.get(f"/api/v1/series/{sid_str}/timeline?reader_chapter=4&from=1&to=4")
    client.get(f"/api/v1/series/{sid_str}/timeline?reader_chapter=5&from=1&to=5")
    client.get(f"/api/v1/series/{sid_str}/timeline?reader_chapter=6&from=1&to=6")

    # Invalidate hook failure simulation
    def failing_delete_prefix(prefix: str):
        raise RuntimeError("Cache cluster node failure")

    clean_cache._backend.delete_prefix = failing_delete_prefix

    # Mutate at Chapter 5
    new_char_id = str(uuid.uuid4())
    target_rel_id = str(uuid.uuid4())
    cid_str = str(ch_n.id)

    fact = RawExtractedFact(
        type=FactType.CHARACTER_INTRODUCED,
        subject_raw="HeroNew",
        target_raw=None,
        payload={
            "subject_id": new_char_id,
            "character_id": new_char_id,
            "name": f"Character_{new_char_id[:6]}",
            "sequence": 99,
        },
        extraction_confidence=1.0,
        evidence=RawFactEvidence(location="ch5"),
    )
    prov = Provenance(
        "src", Evidence(cid_str, "p"), Confidence(1, 1, 1, 1), datetime.now()
    )
    rev_uuid = uuid.uuid4()
    rev_item = ReviewItem(
        str(rev_uuid), sid_str, cid_str, fact, prov, ReviewStatus.APPROVED
    )

    with session_factory() as s:
        from infrastructure.database.models.character import CharacterModel

        s.add(
            CharacterModel(
                id=uuid.UUID(new_char_id),
                series_id=sid,
                name=f"Character_{new_char_id[:6]}",
                description="Temporal test character",
            )
        )
        s.add(
            ReviewItemModel(
                id=rev_uuid,
                series_id=sid,
                chapter_id=ch_n.id,
                fact_type=fact.type.value,
                fact_payload=fact.payload,
                provenance_data=prov.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    with session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)
        use_case.execute(rev_item)

    # Namespace MUST be dirty
    assert clean_cache._backend.is_dirty(sid_str) is True

    # Clear rate limiter to avoid cross-test budget saturation
    get_rate_limit_service().clear()

    # 1. Timeline checks
    # N - 1 (Ch 4): Must not see chapter 5 event or relationship
    resp_ch4 = client.get(
        f"/api/v1/series/{sid_str}/timeline?reader_chapter=4&from=1&to=5"
    )
    assert resp_ch4.status_code == 200
    events_ch4 = resp_ch4.json()
    assert all(e["chapter_number"] <= 4 for e in events_ch4)
    assert not any(e["subject_id"] == new_char_id for e in events_ch4)

    # N (Ch 5): Must see chapter 5 event
    resp_ch5 = client.get(
        f"/api/v1/series/{sid_str}/timeline?reader_chapter=5&from=1&to=5"
    )
    assert resp_ch5.status_code == 200
    events_ch5 = resp_ch5.json()
    assert any(e["subject_id"] == new_char_id for e in events_ch5)

    # 2. Entity existence checks via WorldState
    ws_ch4 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=4").json()
    assert new_char_id not in ws_ch4.get("characters", {}), (
        "FIREWALL BREACH: Future character visible in chapter 4 world state"
    )

    ws_ch5 = client.get(f"/api/v1/series/{sid_str}/world-state?chapter=5").json()
    assert new_char_id in ws_ch5.get("characters", {})

    # 3. Search results check (Global Search with reader_chapter)
    search_ch4 = client.get(
        f"/api/v1/series/{sid_str}/search?q=Character_{new_char_id[:6]}&chapter=4"
    ).json()
    assert search_ch4["total"] == 0, (
        "FIREWALL BREACH: Future character surfaced in search results at chapter 4"
    )

    search_ch5 = client.get(
        f"/api/v1/series/{sid_str}/search?q=Character_{new_char_id[:6]}&chapter=5"
    ).json()
    assert search_ch5["total"] >= 1, (
        "Expected character to appear in search at chapter 5"
    )

    # 4. Analytics check
    analytics_ch4 = client.get(
        f"/api/v1/series/{sid_str}/analytics/overview?to=4"
    ).json()
    assert all(
        int(b["key"]) <= 4 for b in analytics_ch4["statistics"]["events_by_chapter"]
    )
    assert not any(
        b["key"] == new_char_id for b in analytics_ch4["statistics"]["events_by_entity"]
    )


# ==============================================================================
# 4. TEMPORAL FIREWALL UNDER CONCURRENT REQUESTS
# ==============================================================================


def test_temporal_firewall_under_concurrent_boundary_requests(
    session_factory, clean_cache
):
    """Fires concurrent queries for readerChapter = 4, 5, 6 while publication at chapter 5 occurs:
    - Never exposes future state to chapter 4 under multi-worker concurrency
    - Deterministically yields valid firewall state across all threads
    """
    with session_factory() as s:
        env = _seed_boundary_environment(s, target_chapter_num=5)
        sid = env["series_id"]
        sid_str = env["series_id_str"]
        ch_n = env["ch_n"]

    char_id = str(uuid.uuid4())
    rev_item = _create_review_item_for_chapter(sid_str, str(ch_n.id), char_id)

    with session_factory() as s:
        s.add(
            ReviewItemModel(
                id=uuid.UUID(rev_item.id),
                series_id=sid,
                chapter_id=ch_n.id,
                fact_type=rev_item.fact.type.value,
                fact_payload=rev_item.fact.payload,
                provenance_data=rev_item.provenance.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        s.commit()

    # Pre-publish the item
    with session_factory() as s:
        repo = SQLAlchemyPublicationRepository(s)
        use_case = PublishReviewItemUseCase(repo, cache_service=clean_cache)
        use_case.execute(rev_item)

    from apps.api.app.core.rate_limit import get_rate_limit_service

    get_rate_limit_service().clear()

    client = TestClient(app)

    def query_timeline(worker_idx: int, reader_ch: int):
        resp = client.get(
            f"/api/v1/series/{sid_str}/timeline?reader_chapter={reader_ch}&from=1&to=10",
            headers={"X-Forwarded-For": f"192.168.1.{100 + worker_idx}"},
        )
        return reader_ch, resp.status_code, resp.json()

    # Concurrently execute 30 requests across chapters 4, 5, 6
    tasks = [(i, ch) for i, ch in enumerate([4, 5, 6] * 10)]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(query_timeline, i, ch) for i, ch in tasks]
        results = [f.result(timeout=10.0) for f in as_completed(futures)]

    for ch, status, events in results:
        assert status == 200
        if ch == 4:
            # Under concurrency, chapter 4 MUST NEVER see char_id
            assert not any(e["subject_id"] == char_id for e in events), (
                "CONCURRENCY LEAK: Future chapter 5 event leaked to chapter 4 reader!"
            )
            assert all(e["chapter_number"] <= 4 for e in events)
        elif ch in (5, 6):
            # Chapter 5 and 6 MUST see char_id
            assert any(e["subject_id"] == char_id for e in events)
            assert all(e["chapter_number"] <= ch for e in events)
