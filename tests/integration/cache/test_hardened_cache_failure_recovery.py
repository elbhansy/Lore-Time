"""Harden Cache Failure Recovery Integration Tests (COMMAND 10).

Using the existing Phase 4.8 cache architecture:
Simulate cache invalidation failure after successful DB commit in real PostgreSQL.

Verify:
1. DB COMMIT remains authoritative.
2. The successful transaction is NOT rolled back.
3. Cache namespace becomes dirty/bypassed according to the existing policy.
4. Subsequent reads recover from PostgreSQL.
5. No stale temporal data becomes visible.
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
from apps.api.app.application.timeline.get_timeline_events import (
    GetTimelineEventsUseCase,
)
from apps.api.app.application.timeline.get_world_state import (
    GetWorldStateUseCase,
)
from apps.api.app.config import get_settings
from apps.api.app.core.cache import CacheService, reset_cache_service_for_testing
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
from packages.domain.services.event_applier import EventApplier
from packages.domain.services.world_state_builder import WorldStateBuilder
from tests.integration.cache.seed_helper import seed_test_series


@pytest.fixture
def clean_cache():
    """Provides an isolated clean CacheService and registers it globally for testing."""
    service = CacheService()
    reset_cache_service_for_testing(service)
    yield service
    service.clear()
    reset_cache_service_for_testing(None)


def test_cache_invalidation_failure_preserves_db_commit_and_bypasses_dirty_cache(
    clean_cache,
):
    """COMMAND 10: Simulate cache invalidation failure after successful DB commit.

    Verifies:
    1. DB COMMIT remains authoritative.
    2. The successful transaction is NOT rolled back.
    3. Cache namespace becomes dirty/bypassed according to the existing policy.
    4. Subsequent reads recover from PostgreSQL.
    5. No stale temporal data becomes visible.
    """
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()

    try:
        # Step 0: Seed baseline series (5 chapters, 2 events each)
        series_id_str = seed_test_series(session, num_chapters=5, events_per_chapter=2)
        sid = uuid.UUID(series_id_str)
        chapter = session.query(ChapterModel).filter_by(series_id=sid, number=3).first()
        assert chapter is not None

        series_repo = SQLAlchemySeriesRepository(session)
        event_repo = SQLAlchemyEventRepository(session)
        builder = WorldStateBuilder(EventApplier())

        ws_uc = GetWorldStateUseCase(
            series_repo, event_repo, builder, cache_service=clean_cache
        )
        timeline_uc = GetTimelineEventsUseCase(
            series_repo, event_repo, cache_service=clean_cache
        )

        # Step 1: Warm cache at reader_chapter=3 for both WorldState and Timeline
        initial_ws = ws_uc.execute(sid, reader_chapter=3)
        initial_timeline = timeline_uc.execute(
            sid, reader_chapter=3, from_chapter=1, to_chapter=3
        )
        initial_char_count = len(initial_ws.characters)
        initial_event_count = len(initial_timeline)

        assert clean_cache.stats()["entries"] >= 2, "Cache must contain warm entries"
        assert not clean_cache._backend.is_dirty(series_id_str), (
            "Namespace must initially be clean"
        )

        # Step 2: Simulate cache invalidation failure by hooking delete_prefix to raise
        def failing_delete_prefix(prefix: str):
            raise RuntimeError(
                "CRITICAL: Redis / Memory cache node unavailable during purge"
            )

        clean_cache._backend.delete_prefix = failing_delete_prefix

        # Step 3: Prepare a new review item representing a canonical publication at chapter 3
        pub_repo = SQLAlchemyPublicationRepository(session)
        publish_uc = PublishReviewItemUseCase(pub_repo, cache_service=clean_cache)

        new_char_id = str(uuid.uuid4())
        fact = RawExtractedFact(
            type=FactType.CHARACTER_INTRODUCED,
            subject_raw="New Invalidation Hero",
            target_raw=None,
            payload={
                "subject_id": new_char_id,
                "name": "New Invalidation Hero",
                "character_id": new_char_id,
                "sequence": 99,
            },
            extraction_confidence=1.0,
            evidence=RawFactEvidence(location="ch3 p10"),
        )
        prov = Provenance(
            source_id="provenance_cache_harden",
            evidence=Evidence(chapter_id=str(chapter.id), location="ch3 p10"),
            confidence=Confidence(1.0, 1.0, 1.0, 1.0),
            captured_at=datetime.now(),
        )
        rev_uuid = uuid.uuid4()
        session.add(
            ReviewItemModel(
                id=rev_uuid,
                series_id=sid,
                chapter_id=chapter.id,
                fact_type=fact.type.value,
                fact_payload=fact.payload,
                provenance_data=prov.to_dict(),
                status=ReviewStatus.APPROVED.value,
            )
        )
        session.commit()

        review_item = ReviewItem(
            id=str(rev_uuid),
            series_id=series_id_str,
            chapter_id=str(chapter.id),
            fact=fact,
            provenance=prov,
            status=ReviewStatus.APPROVED,
        )

        # Step 4: Execute publication.
        # Although cache invalidation will crash, the use case MUST NOT raise or abort the publication.
        publish_uc.execute(review_item)

        # ======================================================================
        # INVARIANT 1: DB COMMIT remains authoritative & transaction NOT rolled back
        # ======================================================================
        # Open an independent verification session directly against PostgreSQL
        with session_factory() as verify_session:
            # Canonical event exists in PostgreSQL
            db_event = (
                verify_session.query(EventModel)
                .filter_by(series_id=sid, subject_id=uuid.UUID(new_char_id))
                .first()
            )
            assert db_event is not None, (
                "PostgreSQL commit failed or was incorrectly rolled back!"
            )
            assert db_event.type == FactType.CHARACTER_INTRODUCED.value

            # Publication record exists in PostgreSQL with PUBLISHED status
            db_record = (
                verify_session.query(PublicationRecordModel)
                .filter_by(review_item_id=rev_uuid)
                .first()
            )
            assert db_record is not None
            assert db_record.status == PublicationStatus.PUBLISHED.value

            # Review item status in PostgreSQL is PUBLISHED
            db_item = verify_session.query(ReviewItemModel).filter_by(id=rev_uuid).one()
            assert db_item.status == ReviewStatus.PUBLISHED.value

        # ======================================================================
        # INVARIANT 2: Cache namespace becomes dirty / bypassed according to policy
        # ======================================================================
        assert clean_cache._backend.is_dirty(series_id_str) is True, (
            "Cache namespace must be marked DIRTY upon invalidation failure"
        )

        # ======================================================================
        # INVARIANT 3: Subsequent reads recover from PostgreSQL (no stale data)
        # ======================================================================
        # Query WorldState via use case
        recovered_ws = ws_uc.execute(sid, reader_chapter=3)
        assert len(recovered_ws.characters) == initial_char_count + 1
        assert any(
            str(k.value) == new_char_id for k in recovered_ws.characters.keys()
        ), "New character must be visible in WorldState recovered from PostgreSQL"

        # Query Timeline events via use case
        recovered_timeline = timeline_uc.execute(
            sid, reader_chapter=3, from_chapter=1, to_chapter=3
        )
        assert len(recovered_timeline) == initial_event_count + 1
        assert any(
            str(e.event.subject_id.value) == new_char_id for e in recovered_timeline
        ), "New event must be visible in Timeline recovered from PostgreSQL"

        # ======================================================================
        # INVARIANT 4: Full API Integration verification via FastAPI TestClient
        # ======================================================================
        client = TestClient(app)
        api_resp = client.get(
            f"/api/v1/series/{series_id_str}/timeline?reader_chapter=3&from=1&to=3"
        )
        assert api_resp.status_code == 200
        events_payload = api_resp.json()
        assert len(events_payload) == initial_event_count + 1
        assert any(e["subject_id"] == new_char_id for e in events_payload), (
            "API endpoint must return fresh PostgreSQL data, bypassing stale cache"
        )

        # Temporal firewall boundary check: request for chapter 2 cannot see the chapter 3 event
        api_ch2_resp = client.get(
            f"/api/v1/series/{series_id_str}/timeline?reader_chapter=2&from=1&to=2"
        )
        assert api_ch2_resp.status_code == 200
        ch2_events = api_ch2_resp.json()
        assert not any(e["subject_id"] == new_char_id for e in ch2_events), (
            "Temporal spoiler firewall invariant violated: chapter 3 event leaked into chapter 2 view"
        )

    finally:
        session.close()
        engine.dispose()
